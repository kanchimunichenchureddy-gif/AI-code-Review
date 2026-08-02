import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from analysis.similarity.engine import similarity_engine
from backend.app.models.submission import Submission
from backend.app.models.similarity import SimilarityResultModel


class SimilarityPipelineService:
    def check_assignment_plagiarism(self, db: Session, assignment_id: int) -> List[SimilarityResultModel]:
        # Get all completed submissions for assignment
        submissions = (
            db.query(Submission)
            .filter(Submission.assignment_id == assignment_id)
            .all()
        )

        if len(submissions) < 2:
            return []

        # Clear existing similarity results for these submissions
        sub_ids = [s.id for s in submissions]
        db.query(SimilarityResultModel).filter(SimilarityResultModel.submission_id.in_(sub_ids)).delete(synchronize_session=False)
        db.flush()

        created_results: List[SimilarityResultModel] = []

        # Pairwise comparison
        for i in range(len(submissions)):
            sub1 = submissions[i]
            code1 = "\n".join(f.content for f in sub1.files)
            max_sim = 0.0
            highest_tier = "LOW"

            for j in range(len(submissions)):
                if i == j or submissions[j].student_id == sub1.student_id:
                    continue  # Skip self or same student attempts

                sub2 = submissions[j]
                code2 = "\n".join(f.content for f in sub2.files)

                comp_res = similarity_engine.compare_submissions(code1, code2)

                if comp_res.similarity_score > max_sim:
                    max_sim = comp_res.similarity_score
                    highest_tier = comp_res.tier

                sim_model = SimilarityResultModel(
                    submission_id=sub1.id,
                    compared_submission_id=sub2.id,
                    similarity_score=comp_res.similarity_score,
                    tier=comp_res.tier,
                    token_similarity=comp_res.token_similarity,
                    ast_similarity=comp_res.ast_similarity,
                    human_review_recommended=comp_res.human_review_recommended,
                    matching_regions_json=json.dumps(comp_res.matching_regions),
                )
                db.add(sim_model)
                created_results.append(sim_model)

            sub1.plagiarism_similarity_tier = highest_tier

        db.commit()
        return created_results


similarity_pipeline_service = SimilarityPipelineService()
