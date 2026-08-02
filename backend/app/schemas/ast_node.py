from typing import Optional
from pydantic import BaseModel, ConfigDict


class ASTNodeResponse(BaseModel):
    id: int
    submission_id: int
    file_path: str
    node_id: str
    node_type: str
    identifier: Optional[str] = None
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    parent_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
