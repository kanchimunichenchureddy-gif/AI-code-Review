from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SimilarityResultResponse(BaseModel):
    id: int
    submission_id: int
    compared_submission_id: int
    similarity_score: float
    tier: str
    token_similarity: float
    ast_similarity: float
    human_review_recommended: bool
    matching_regions_json: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
