from typing import List, Dict, Any
from sqlalchemy.orm import Session

from analysis.parsers.ast_store import ast_store_service
from analysis.complexity.engine import complexity_engine
from analysis.static.engine import static_analysis_engine
from analysis.security.engine import security_analysis_engine
from analysis.rubrics.evaluator import rubric_evaluator
from backend.app.models.submission import Submission, SubmissionStatus
from backend.app.models.rubric import Rubric
from backend.app.models.finding import StaticFindingModel, SecurityFindingModel, ComplexityMetricModel


class FullAnalysisService:
    def run_full_analysis(self, db: Session, submission: Submission) -> Dict[str, Any]:
        submission.status = SubmissionStatus.ANALYZING
        db.commit()

        # Step 1: Parse and store AST nodes
        ast_nodes_db = ast_store_service.parse_and_store_submission(db, submission)

        # Clear existing findings & metrics for this submission
        db.query(StaticFindingModel).filter(StaticFindingModel.submission_id == submission.id).delete()
        db.query(SecurityFindingModel).filter(SecurityFindingModel.submission_id == submission.id).delete()
        db.query(ComplexityMetricModel).filter(ComplexityMetricModel.submission_id == submission.id).delete()
        db.flush()

        created_static_findings: List[StaticFindingModel] = []
        created_security_findings: List[SecurityFindingModel] = []
        created_metrics: List[ComplexityMetricModel] = []

        for sub_file in submission.files:
            # Step 2: Compute Complexity & Metrics
            calc_metrics = complexity_engine.compute_file_metrics(
                file_path=sub_file.filename,
                content=sub_file.content,
                ast_nodes=[]
            )

            metric_db = ComplexityMetricModel(
                submission_id=submission.id,
                file_path=sub_file.filename,
                function_name=calc_metrics.function_name,
                cyclomatic_complexity=calc_metrics.cyclomatic_complexity,
                cognitive_complexity=calc_metrics.cognitive_complexity,
                maintainability_index=calc_metrics.maintainability_index,
                lines_of_code=calc_metrics.lines_of_code,
                nesting_depth=calc_metrics.nesting_depth,
            )
            db.add(metric_db)
            created_metrics.append(metric_db)

            # Step 3: Run Static Analysis Rules
            findings_data = static_analysis_engine.analyze_file(
                file_path=sub_file.filename,
                content=sub_file.content,
                ast_nodes=[]
            )

            for f_data in findings_data:
                finding_db = StaticFindingModel(
                    submission_id=submission.id,
                    file_path=sub_file.filename,
                    rule_id=f_data.rule_id,
                    category=f_data.category,
                    severity=f_data.severity,
                    message=f_data.message,
                    line_start=f_data.line_start,
                    line_end=f_data.line_end,
                    col_start=f_data.col_start,
                    col_end=f_data.col_end,
                    evidence_snippet=f_data.evidence_snippet,
                )
                db.add(finding_db)
                created_static_findings.append(finding_db)

            # Step 4: Run Security SAST Engine
            sec_findings_data = security_analysis_engine.scan_file(
                file_path=sub_file.filename,
                content=sub_file.content,
            )

            for s_data in sec_findings_data:
                sec_db = SecurityFindingModel(
                    submission_id=submission.id,
                    file_path=sub_file.filename,
                    cve_or_rule=s_data.cve_or_rule,
                    vulnerability_type=s_data.vulnerability_type,
                    severity=s_data.severity,
                    description=s_data.description,
                    line_number=s_data.line_number,
                    evidence_snippet=s_data.evidence_snippet,
                )
                db.add(sec_db)
                created_security_findings.append(sec_db)

        # Step 5: Evaluate Rubric and calculate final submission score
        rubric = db.query(Rubric).filter(Rubric.assignment_id == submission.assignment_id).first()
        if rubric:
            eval_res = rubric_evaluator.evaluate_rubric(
                rubric=rubric,
                max_score=float(submission.assignment.max_score),
                static_findings=created_static_findings,
                security_findings=created_security_findings,
                complexity_metrics=created_metrics,
            )
            submission.score = eval_res.final_score
        else:
            # Default score when no rubric is defined: deduct for static & security findings
            total_penalty = (len(created_static_findings) * 2.0) + (len(created_security_findings) * 10.0)
            submission.score = max(0.0, float(submission.assignment.max_score) - total_penalty)

        submission.status = SubmissionStatus.COMPLETED
        db.commit()

        return {
            "status": "COMPLETED",
            "score": submission.score,
            "static_findings_count": len(created_static_findings),
            "security_findings_count": len(created_security_findings),
            "metrics_count": len(created_metrics),
        }


full_analysis_service = FullAnalysisService()
