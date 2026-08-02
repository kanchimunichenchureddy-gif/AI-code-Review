from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class ASTNodeModel(Base):
    __tablename__ = "ast_nodes"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(1024), nullable=False)
    node_id = Column(String(100), nullable=False, index=True)
    node_type = Column(String(100), nullable=False, index=True)
    identifier = Column(String(255), nullable=True, index=True)
    start_line = Column(Integer, nullable=False)
    start_col = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    end_col = Column(Integer, nullable=False)
    parent_id = Column(String(100), nullable=True)
    attributes_json = Column(Text, nullable=True)

    submission = relationship("Submission", backref="ast_nodes")
