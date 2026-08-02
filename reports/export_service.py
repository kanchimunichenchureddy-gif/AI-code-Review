import csv
import io
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.models.course import Course
from backend.app.models.submission import Submission
from backend.app.models.finding import StaticFindingModel, SecurityFindingModel, ComplexityMetricModel, FeedbackModel
from backend.app.models.rubric import Rubric
from analysis.rubrics.evaluator import rubric_evaluator


class ReportExportService:
    def generate_csv_gradebook(self, db: Session, course_id: int) -> str:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return ""

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Course Code", "Course Title", "Student Name", "Student Email",
            "Assignment Title", "Attempt Number", "Submission Status",
            "Score", "Plagiarism Tier", "Submitted At"
        ])

        for assign in course.assignments:
            submissions = (
                db.query(Submission)
                .filter(Submission.assignment_id == assign.id)
                .order_by(Submission.student_id, Submission.attempt_number.desc())
                .all()
            )

            for sub in submissions:
                writer.writerow([
                    course.code,
                    course.title,
                    sub.student.full_name,
                    sub.student.email,
                    assign.title,
                    sub.attempt_number,
                    sub.status.value,
                    sub.score if sub.score is not None else "N/A",
                    sub.plagiarism_similarity_tier,
                    sub.created_at.isoformat() if sub.created_at else "",
                ])

        return output.getvalue()

    def generate_submission_report_json(self, db: Session, submission: Submission) -> Dict[str, Any]:
        static_f = db.query(StaticFindingModel).filter(StaticFindingModel.submission_id == submission.id).all()
        sec_f = db.query(SecurityFindingModel).filter(SecurityFindingModel.submission_id == submission.id).all()
        metrics = db.query(ComplexityMetricModel).filter(ComplexityMetricModel.submission_id == submission.id).all()
        feedback = db.query(FeedbackModel).filter(FeedbackModel.submission_id == submission.id).all()

        rubric = db.query(Rubric).filter(Rubric.assignment_id == submission.assignment_id).first()
        rubric_eval_data = None
        if rubric:
            eval_res = rubric_evaluator.evaluate_rubric(
                rubric=rubric,
                max_score=float(submission.assignment.max_score),
                static_findings=static_f,
                security_findings=sec_f,
                complexity_metrics=metrics,
            )
            rubric_eval_data = {
                "total_weight": eval_res.total_weight,
                "earned_points": eval_res.earned_points,
                "final_score": eval_res.final_score,
                "rule_results": [
                    {
                        "rule_code": r.rule_code,
                        "category": r.category,
                        "weight": r.weight,
                        "violations_count": r.violations_count,
                        "deduction": r.deduction,
                        "score": r.score,
                        "is_mandatory": r.is_mandatory,
                        "passed": r.passed,
                        "details": r.details,
                    }
                    for r in eval_res.rule_results
                ]
            }

        return {
            "submission_id": submission.id,
            "assignment_id": submission.assignment_id,
            "assignment_title": submission.assignment.title,
            "student_id": submission.student_id,
            "student_name": submission.student.full_name,
            "student_email": submission.student.email,
            "status": submission.status.value,
            "attempt_number": submission.attempt_number,
            "score": submission.score,
            "plagiarism_tier": submission.plagiarism_similarity_tier,
            "created_at": submission.created_at.isoformat() if submission.created_at else None,
            "files": [
                {"id": f.id, "filename": f.filename, "language": f.language, "file_hash": f.file_hash}
                for f in submission.files
            ],
            "static_findings": [
                {
                    "rule_id": sf.rule_id,
                    "category": sf.category,
                    "severity": sf.severity,
                    "message": sf.message,
                    "line_start": sf.line_start,
                    "line_end": sf.line_end,
                    "evidence_snippet": sf.evidence_snippet,
                }
                for sf in static_f
            ],
            "security_findings": [
                {
                    "cve_or_rule": sec.cve_or_rule,
                    "vulnerability_type": sec.vulnerability_type,
                    "severity": sec.severity,
                    "description": sec.description,
                    "line_number": sec.line_number,
                    "evidence_snippet": sec.evidence_snippet,
                }
                for sec in sec_f
            ],
            "complexity_metrics": [
                {
                    "file_path": m.file_path,
                    "cyclomatic_complexity": m.cyclomatic_complexity,
                    "cognitive_complexity": m.cognitive_complexity,
                    "maintainability_index": m.maintainability_index,
                    "lines_of_code": m.lines_of_code,
                    "nesting_depth": m.nesting_depth,
                }
                for m in metrics
            ],
            "rubric_evaluation": rubric_eval_data,
            "feedback_cards": [
                {
                    "category": fb.category,
                    "title": fb.title,
                    "what_text": fb.what_text,
                    "why_text": fb.why_text,
                    "how_to_fix_text": fb.how_to_fix_text,
                    "example_code": fb.example_code,
                    "file_path": fb.file_path,
                    "line_number": fb.line_number,
                }
                for fb in feedback
            ],
        }


report_export_service = ReportExportService()
