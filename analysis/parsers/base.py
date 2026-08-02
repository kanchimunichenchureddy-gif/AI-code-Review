from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Point:
    line: int
    column: int


@dataclass
class ASTNode:
    node_id: str
    node_type: str
    identifier: Optional[str]
    start_point: Point
    end_point: Point
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "identifier": self.identifier,
            "start_point": {"line": self.start_point.line, "column": self.start_point.column},
            "end_point": {"line": self.end_point.line, "column": self.end_point.column},
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "attributes": self.attributes,
        }


class BaseParser(ABC):
    @abstractmethod
    def parse_code(self, source_code: str, language: str) -> List[ASTNode]:
        """Parses source code into a standardized list of ASTNode instances."""
        pass
