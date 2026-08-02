import ast
import re
from typing import List, Dict, Optional
from analysis.parsers.base import BaseParser, ASTNode, Point

try:
    from tree_sitter import Language, Parser
except ImportError:  # Tree-sitter is an optional parser backend.
    Language = None
    Parser = None

try:
    import tree_sitter_python
except ImportError:
    tree_sitter_python = None

try:
    import tree_sitter_javascript
except ImportError:
    tree_sitter_javascript = None

try:
    import tree_sitter_java
except ImportError:
    tree_sitter_java = None

try:
    import tree_sitter_c
except ImportError:
    tree_sitter_c = None

try:
    import tree_sitter_cpp
except ImportError:
    tree_sitter_cpp = None


class TreeSitterParser(BaseParser):
    def __init__(self):
        self.languages: Dict[str, Language] = {}

        if Language is None:
            return

        try:
            if tree_sitter_python is None:
                raise ImportError
            self.languages["python"] = Language(tree_sitter_python.language())
        except Exception:
            pass

        try:
            if tree_sitter_javascript is None:
                raise ImportError
            self.languages["javascript"] = Language(tree_sitter_javascript.language())
            self.languages["js"] = self.languages["javascript"]
        except Exception:
            pass

        try:
            if tree_sitter_java is None:
                raise ImportError
            self.languages["java"] = Language(tree_sitter_java.language())
        except Exception:
            pass

        try:
            if tree_sitter_c is None:
                raise ImportError
            self.languages["c"] = Language(tree_sitter_c.language())
        except Exception:
            pass

        try:
            if tree_sitter_cpp is None:
                raise ImportError
            self.languages["cpp"] = Language(tree_sitter_cpp.language())
            self.languages["c++"] = self.languages["cpp"]
        except Exception:
            pass

    def get_parser(self, language: str) -> Optional[Parser]:
        if Parser is None:
            return None
        lang_str = language.lower()
        if lang_str in self.languages:
            parser = Parser(self.languages[lang_str])
            return parser
        return None

    def parse_code(self, source_code: str, language: str) -> List[ASTNode]:
        parser = self.get_parser(language)
        if not parser:
            return self._parse_with_fallback(source_code, language)

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

    def _parse_with_fallback(self, source_code: str, language: str) -> List[ASTNode]:
        lang = (language or "").lower()
        if lang == "python":
            return self._parse_python_ast(source_code)
        return self._parse_common_signatures(source_code, lang)

    def _parse_python_ast(self, source_code: str) -> List[ASTNode]:
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return self._parse_common_signatures(source_code, "python")

        nodes: List[ASTNode] = []
        counter = 0

        def add_node(node_type: str, identifier: Optional[str], start_line: int, end_line: int, parent_id: Optional[str]) -> str:
            nonlocal counter
            node_id = f"ast_node_{counter}"
            counter += 1
            ast_node = ASTNode(
                node_id=node_id,
                node_type=node_type,
                identifier=identifier,
                start_point=Point(line=start_line, column=0),
                end_point=Point(line=end_line, column=0),
                parent_id=parent_id,
                children_ids=[],
                attributes={"backend": "python_ast"},
            )
            nodes.append(ast_node)
            if parent_id:
                parent = next((n for n in nodes if n.node_id == parent_id), None)
                if parent:
                    parent.children_ids.append(node_id)
            return node_id

        root_id = add_node("module", None, 1, max(1, len(source_code.splitlines())), None)

        def visit(py_node, parent_id: str) -> None:
            node_type = self._python_node_type(py_node)
            if not node_type:
                for child in ast.iter_child_nodes(py_node):
                    visit(child, parent_id)
                return

            identifier = getattr(py_node, "name", None)
            start_line = getattr(py_node, "lineno", 1)
            end_line = getattr(py_node, "end_lineno", start_line)
            current_id = add_node(node_type, identifier, start_line, end_line, parent_id)

            for child in ast.iter_child_nodes(py_node):
                visit(child, current_id)

        for child in ast.iter_child_nodes(tree):
            visit(child, root_id)

        return nodes

    def _python_node_type(self, py_node) -> Optional[str]:
        if isinstance(py_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return "function_definition"
        if isinstance(py_node, ast.ClassDef):
            return "class_definition"
        if isinstance(py_node, (ast.For, ast.AsyncFor)):
            return "for_statement"
        if isinstance(py_node, ast.While):
            return "while_statement"
        if isinstance(py_node, ast.If):
            return "if_statement"
        if isinstance(py_node, ast.Call):
            return "call"
        if isinstance(py_node, ast.Assign):
            return "assignment"
        if isinstance(py_node, ast.Return):
            return "return_statement"
        return None

    def _parse_common_signatures(self, source_code: str, language: str = "") -> List[ASTNode]:
        nodes = [
            ASTNode(
                node_id="ast_node_0",
                node_type="source_file",
                identifier=None,
                start_point=Point(line=1, column=0),
                end_point=Point(line=max(1, len(source_code.splitlines())), column=0),
                attributes={"backend": "regex_fallback"},
            )
        ]

        function_node_type = "function_declaration" if language in {"javascript", "js"} else "function_definition"
        patterns = [
            ("class_definition", re.compile(r"\bclass\s+([A-Za-z_]\w*)")),
            (function_node_type, re.compile(r"\b(?:def|function)\s+([A-Za-z_]\w*)\s*\(")),
            ("function_definition", re.compile(r"^\s*(?:[A-Za-z_][\w:<>\*\&\[\]]+\s+)+([A-Za-z_]\w*)\s*\(")),
        ]

        for line_number, line in enumerate(source_code.splitlines(), start=1):
            for node_type, pattern in patterns:
                match = pattern.search(line)
                if not match:
                    continue
                node_id = f"ast_node_{len(nodes)}"
                nodes[0].children_ids.append(node_id)
                nodes.append(
                    ASTNode(
                        node_id=node_id,
                        node_type=node_type,
                        identifier=match.group(1),
                        start_point=Point(line=line_number, column=match.start()),
                        end_point=Point(line=line_number, column=len(line)),
                        parent_id="ast_node_0",
                        attributes={"backend": "regex_fallback"},
                    )
                )
                break

        return nodes
