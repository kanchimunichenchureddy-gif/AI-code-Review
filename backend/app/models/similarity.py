from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class SimilarityResultModel(Base):
    __tablename__ = "similarity_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    compared_submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    tier = Column(String(50), nullable=False, default="LOW")
    token_similarity = Column(Float, nullable=False)
    ast_similarity = Column(Float, nullable=False)
    human_review_recommended = Column(Boolean, default=False, nullable=False)
    matching_regions_json = Column(Text, nullable=True)

    submission = relationship("Submission", foreign_keys=[submission_id], backref="similarity_results")
    compared_submission = relationship("Submission", foreign_keys=[compared_submission_id])
