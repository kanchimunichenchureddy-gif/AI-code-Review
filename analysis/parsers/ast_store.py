import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from analysis.parsers.treesitter_parser import TreeSitterParser
from analysis.parsers.detector import language_detector
from backend.app.models.submission import Submission
from backend.app.models.ast_node import ASTNodeModel


class ASTStoreService:
    def __init__(self):
        self.parser = TreeSitterParser()

    def parse_and_store_submission(self, db: Session, submission: Submission) -> List[ASTNodeModel]:
        # Delete any pre-existing AST nodes for this submission
        db.query(ASTNodeModel).filter(ASTNodeModel.submission_id == submission.id).delete()
        db.flush()

        created_nodes: List[ASTNodeModel] = []

        for sub_file in submission.files:
            # Detect language if not specified or generic
            lang = sub_file.language
            if not lang or lang == "unknown":
                lang = language_detector.detect_language(sub_file.filename, sub_file.content)
                sub_file.language = lang

            parsed_ast_nodes = self.parser.parse_code(sub_file.content, lang)

            for ast_n in parsed_ast_nodes:
                node_model = ASTNodeModel(
                    submission_id=submission.id,
                    file_path=sub_file.filename,
                    node_id=ast_n.node_id,
                    node_type=ast_n.node_type,
                    identifier=ast_n.identifier,
                    start_line=ast_n.start_point.line,
                    start_col=ast_n.start_point.column,
                    end_line=ast_n.end_point.line,
                    end_col=ast_n.end_point.column,
                    parent_id=ast_n.parent_id,
                    attributes_json=json.dumps(ast_n.attributes),
                )
                db.add(node_model)
                created_nodes.append(node_model)

        db.commit()
        return created_nodes


ast_store_service = ASTStoreService()
