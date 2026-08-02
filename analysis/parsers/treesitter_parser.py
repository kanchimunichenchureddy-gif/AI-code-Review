import tree_sitter
from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_java
import tree_sitter_c
import tree_sitter_cpp
from typing import List, Dict, Optional
from analysis.parsers.base import BaseParser, ASTNode, Point


class TreeSitterParser(BaseParser):
    def __init__(self):
        self.languages: Dict[str, Language] = {}

        try:
            self.languages["python"] = Language(tree_sitter_python.language())
        except Exception:
            pass

        try:
            self.languages["javascript"] = Language(tree_sitter_javascript.language())
            self.languages["js"] = self.languages["javascript"]
        except Exception:
            pass

        try:
            self.languages["java"] = Language(tree_sitter_java.language())
        except Exception:
            pass

        try:
            self.languages["c"] = Language(tree_sitter_c.language())
        except Exception:
            pass

        try:
            self.languages["cpp"] = Language(tree_sitter_cpp.language())
            self.languages["c++"] = self.languages["cpp"]
        except Exception:
            pass

    def get_parser(self, language: str) -> Optional[Parser]:
        lang_str = language.lower()
        if lang_str in self.languages:
            parser = Parser(self.languages[lang_str])
            return parser
        return None

    def parse_code(self, source_code: str, language: str) -> List[ASTNode]:
        parser = self.get_parser(language)
        if not parser:
            # Fallback for unsupported language or parser failure
            return []

        bytes_code = source_code.encode("utf-8")
        tree = parser.parse(bytes_code)
        
        nodes: List[ASTNode] = []
        node_counter = 0

        def traverse(ts_node, parent_id: Optional[str] = None) -> str:
            nonlocal node_counter
            current_id = f"ast_node_{node_counter}"
            node_counter += 1

            # Get node identifier if available
            identifier = None
            if ts_node.type in ["function_definition", "function_declarator", "class_definition", "identifier"]:
                # extract identifier text
                identifier = bytes_code[ts_node.start_byte:ts_node.end_byte].decode("utf-8", errors="ignore")

            start_p = Point(line=ts_node.start_point.row + 1, column=ts_node.start_point.column)
            end_p = Point(line=ts_node.end_point.row + 1, column=ts_node.end_point.column)

            ast_node = ASTNode(
                node_id=current_id,
                node_type=ts_node.type,
                identifier=identifier,
                start_point=start_p,
                end_point=end_p,
                parent_id=parent_id,
                children_ids=[],
                attributes={"is_named": ts_node.is_named}
            )
            nodes.append(ast_node)

            for child in ts_node.children:
                child_id = traverse(child, parent_id=current_id)
                ast_node.children_ids.append(child_id)

            return current_id

        traverse(tree.root_node)
        return nodes
