from analysis.parsers.treesitter_parser import TreeSitterParser


def test_tree_sitter_python_parser():
    parser = TreeSitterParser()
    code = """
def calculate_factorial(n):
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)
"""
    nodes = parser.parse_code(code, "python")
    assert len(nodes) > 0
    node_types = [n.node_type for n in nodes]
    assert "function_definition" in node_types


def test_tree_sitter_javascript_parser():
    parser = TreeSitterParser()
    code = """
function add(a, b) {
    return a + b;
}
"""
    nodes = parser.parse_code(code, "javascript")
    assert len(nodes) > 0
    node_types = [n.node_type for n in nodes]
    assert "function_declaration" in node_types


def test_tree_sitter_c_parser():
    parser = TreeSitterParser()
    code = """
int main() {
    int x = 10;
    return 0;
}
"""
    nodes = parser.parse_code(code, "c")
    assert len(nodes) > 0
    node_types = [n.node_type for n in nodes]
    assert "function_definition" in node_types
