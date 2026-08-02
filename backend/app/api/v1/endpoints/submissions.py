from types import SimpleNamespace
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user, require_role
from backend.app.core.storage import storage_manager, StorageSecurityError
from backend.app.models.user import User, RoleEnum
from backend.app.models.assignment import Assignment
from backend.app.models.rubric import Rubric
from backend.app.models.submission import Submission, SubmissionFile, SubmissionStatus
from backend.app.models.ast_node import ASTNodeModel
from backend.app.models.finding import StaticFindingModel, SecurityFindingModel, ComplexityMetricModel, FeedbackModel
from backend.app.models.similarity import SimilarityResultModel
from backend.app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionHistoryResponse,
    SubmissionFileResponse,
    StaticFindingResponse,
    SecurityFindingResponse,
    ComplexityMetricResponse,
    FeedbackResponse,
)
from backend.app.schemas.ast_node import ASTNodeResponse
from backend.app.schemas.rubric_eval import RubricEvaluationResponse
from backend.app.schemas.similarity import SimilarityResultResponse
from analysis.parsers.ast_store import ast_store_service
from analysis.analysis_service import full_analysis_service
from analysis.rubrics.evaluator import rubric_evaluator
from analysis.similarity.similarity_service import similarity_pipeline_service
from ai.service import ai_feedback_service

router = APIRouter()

MAX_SUBMISSION_FILES = 500
MAX_SUBMISSION_TOTAL_BYTES = 10_000_000
MAX_SINGLE_FILE_BYTES = 1_000_000
MAX_ZIP_UPLOAD_BYTES = 50_000_000

# Map assignment language to valid extensions
LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx", ".ts", ".tsx"],
    "java": [".java"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".hpp", ".cc", ".h"],
    "c++": [".cpp", ".hpp", ".cc", ".h"],
    "csharp": [".cs"],
}

ALL_SUPPORTED_EXTENSIONS = sorted({ext for extensions in LANGUAGE_EXTENSIONS.values() for ext in extensions})


def infer_language_from_filename(filename: str, fallback: str) -> str:
    lower_name = filename.lower()
    if lower_name.endswith(".py"):
        return "python"
    if lower_name.endswith((".js", ".jsx", ".ts", ".tsx")):
        return "javascript"
    if lower_name.endswith(".java"):
        return "java"
    if lower_name.endswith((".cpp", ".hpp", ".cc")):
        return "cpp"
    if lower_name.endswith((".c", ".h")):
        return "c"
    if lower_name.endswith(".cs"):
        return "csharp"
    return fallback


def get_latest_attempt_number(db: Session, assignment_id: int, student_id: int) -> tuple[int, int | None]:
    last_sub = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id, Submission.student_id == student_id)
        .order_by(Submission.attempt_number.desc())
        .first()
    )
    if not last_sub:
        return 1, None
    return last_sub.attempt_number + 1, last_sub.id


def validate_submission_payload(files) -> None:
    if len(files) > MAX_SUBMISSION_FILES:
        raise HTTPException(
            status_code=413,
            detail=f"Too many source files. Limit is {MAX_SUBMISSION_FILES} files per review.",
        )

    total_bytes = 0
    for file_in in files:
        content_bytes = len(file_in.content.encode("utf-8"))
        total_bytes += content_bytes
        if content_bytes > MAX_SINGLE_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File '{file_in.filename}' is too large. Limit is {MAX_SINGLE_FILE_BYTES // 1000} KB per file.",
            )

    if total_bytes > MAX_SUBMISSION_TOTAL_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Submission is too large. Limit is {MAX_SUBMISSION_TOTAL_BYTES // 1_000_000} MB of source code per review.",
        )


@router.post("/assignment/{assignment_id}", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission_json(
    assignment_id: int,
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if not submission_in.files:
        raise HTTPException(status_code=400, detail="Submission must contain at least one code file")
    validate_submission_payload(submission_in.files)

    attempt_num, parent_id = get_latest_attempt_number(db, assignment_id, current_user.id)

    submission = Submission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        status=SubmissionStatus.PENDING,
        attempt_number=attempt_num,
        parent_submission_id=parent_id,
    )
    db.add(submission)
    db.flush()

    sub_dir = storage_manager.get_submission_dir(assignment_id, current_user.id, submission.id)
    submission.storage_path = str(sub_dir)

    for f_in in submission_in.files:
        target_path, file_hash = storage_manager.save_file(sub_dir, f_in.filename, f_in.content)
        sub_file = SubmissionFile(
            submission_id=submission.id,
            filename=f_in.filename,
            content=f_in.content,
            language=f_in.language or assignment.language,
            file_hash=file_hash,
        )
        db.add(sub_file)

    db.commit()
    db.refresh(submission)
    return submission


@router.post("/assignment/{assignment_id}/upload", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission_zip(
    assignment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip archive files are supported")

    content_bytes = await file.read()
    if len(content_bytes) > MAX_ZIP_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"ZIP archive is too large. Limit is {MAX_ZIP_UPLOAD_BYTES // 1_000_000} MB. Remove dependencies/build folders or upload a smaller source-only ZIP.",
        )

    allowed_exts = ALL_SUPPORTED_EXTENSIONS
    
    extracted_files = storage_manager.extract_zip_bytes(content_bytes, allowed_exts)
    if not extracted_files:
        raise HTTPException(
            status_code=400,
            detail=f"No valid source files matching extensions {allowed_exts} found in zip archive"
        )
    validate_submission_payload([
        SimpleNamespace(filename=ef["filename"], content=ef["content"])
        for ef in extracted_files
    ])

    attempt_num, parent_id = get_latest_attempt_number(db, assignment_id, current_user.id)

    submission = Submission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        status=SubmissionStatus.PENDING,
        attempt_number=attempt_num,
        parent_submission_id=parent_id,
    )
    db.add(submission)
    db.flush()

    sub_dir = storage_manager.get_submission_dir(assignment_id, current_user.id, submission.id)
    submission.storage_path = str(sub_dir)

    for ef in extracted_files:
        target_path, file_hash = storage_manager.save_file(sub_dir, ef["filename"], ef["content"])
        sub_file = SubmissionFile(
            submission_id=submission.id,
            filename=ef["filename"],
            content=ef["content"],
            language=infer_language_from_filename(ef["filename"], assignment.language),
            file_hash=file_hash,
        )
        db.add(sub_file)

    db.commit()
    db.refresh(submission)
    return submission


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission_detail(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to view this submission")

    return submission


@router.post("/{submission_id}/generate-feedback", response_model=List[FeedbackResponse])
def generate_ai_feedback(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to generate feedback for this submission")

    # Run full analysis if findings don't exist yet
    if not submission.findings and not submission.security_findings and not submission.complexity_metrics:
        full_analysis_service.run_full_analysis(db, submission)
        db.refresh(submission)

    generated_feedback = ai_feedback_service.generate_feedback_for_submission(db, submission)
    return generated_feedback


@router.get("/{submission_id}/feedback", response_model=List[FeedbackResponse])
def get_submission_feedback(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to view feedback")

    feedback_items = db.query(FeedbackModel).filter(FeedbackModel.submission_id == submission_id).all()
    return feedback_items


@router.post("/assignment/{assignment_id}/check-plagiarism", response_model=List[SimilarityResultResponse])
def run_plagiarism_check(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA])),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    results = similarity_pipeline_service.check_assignment_plagiarism(db, assignment_id)
    return results


@router.get("/{submission_id}/plagiarism", response_model=List[SimilarityResultResponse])
def get_submission_plagiarism_results(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to view plagiarism reports")

    results = db.query(SimilarityResultModel).filter(SimilarityResultModel.submission_id == submission_id).all()
    return results


@router.post("/{submission_id}/parse", response_model=List[ASTNodeResponse])
def trigger_ast_parse(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to parse this submission")

    try:
        submission.status = SubmissionStatus.PARSING
        db.commit()

        created_nodes = ast_store_service.parse_and_store_submission(db, submission)

        submission.status = SubmissionStatus.COMPLETED
        db.commit()
    except Exception as exc:
        db.rollback()
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.status = SubmissionStatus.FAILED
            db.commit()
        raise HTTPException(status_code=500, detail=f"AST parse failed: {str(exc)}") from exc

    return created_nodes


@router.post("/{submission_id}/analyze", response_model=SubmissionResponse)
def trigger_full_analysis(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to analyze this submission")

    try:
        full_analysis_service.run_full_analysis(db, submission)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.status = SubmissionStatus.FAILED
            db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}") from exc

    db.refresh(submission)
    return submission


@router.get("/{submission_id}/rubric-evaluation", response_model=RubricEvaluationResponse)
def get_rubric_evaluation(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to view rubric evaluation")

    rubric = db.query(Rubric).filter(Rubric.assignment_id == submission.assignment_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="No rubric defined for this assignment")

    static_f = db.query(StaticFindingModel).filter(StaticFindingModel.submission_id == submission_id).all()
    sec_f = db.query(SecurityFindingModel).filter(SecurityFindingModel.submission_id == submission_id).all()
    metrics = db.query(ComplexityMetricModel).filter(ComplexityMetricModel.submission_id == submission_id).all()

    return rubric_evaluator.evaluate_rubric(
        rubric=rubric,
        max_score=float(submission.assignment.max_score),
        static_findings=static_f,
        security_findings=sec_f,
        complexity_metrics=metrics,
    )


@router.get("/{submission_id}/ast", response_model=List[ASTNodeResponse])
def get_submission_ast_nodes(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to view this AST")

    ast_nodes = db.query(ASTNodeModel).filter(ASTNodeModel.submission_id == submission_id).all()
    return ast_nodes


@router.get("/{submission_id}/findings", response_model=List[StaticFindingResponse])
def get_submission_findings(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to view these findings")

    findings = db.query(StaticFindingModel).filter(StaticFindingModel.submission_id == submission_id).all()
    return findings


@router.get("/{submission_id}/security-findings", response_model=List[SecurityFindingResponse])
def get_submission_security_findings(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to view security findings")

    sec_findings = db.query(SecurityFindingModel).filter(SecurityFindingModel.submission_id == submission_id).all()
    return sec_findings


@router.get("/{submission_id}/metrics", response_model=List[ComplexityMetricResponse])
def get_submission_metrics(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to view these metrics")

    metrics = db.query(ComplexityMetricModel).filter(ComplexityMetricModel.submission_id == submission_id).all()
    return metrics


@router.get("/assignment/{assignment_id}/history", response_model=List[SubmissionHistoryResponse])
def get_submission_history(
    assignment_id: int,
    student_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_student_id = current_user.id
    if student_id and current_user.role in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        target_student_id = student_id

    submissions = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id, Submission.student_id == target_student_id)
        .order_by(Submission.attempt_number.asc())
        .all()
    )
    return submissions


@router.get("/{submission_id}/files/{file_id}", response_model=SubmissionFileResponse)
def get_submission_file(
    submission_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.id != submission.student_id and current_user.role not in [RoleEnum.INSTRUCTOR, RoleEnum.ADMIN, RoleEnum.TA]:
        raise HTTPException(status_code=403, detail="Not authorized to access this file")

    sub_file = db.query(SubmissionFile).filter(
        SubmissionFile.id == file_id, SubmissionFile.submission_id == submission_id
    ).first()
    if not sub_file:
        raise HTTPException(status_code=404, detail="File not found in submission")

    return sub_file
