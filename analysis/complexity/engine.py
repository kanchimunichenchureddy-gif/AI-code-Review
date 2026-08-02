import math
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from analysis.parsers.base import ASTNode


@dataclass
class CalculatedMetrics:
    file_path: str
    function_name: Optional[str]
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    lines_of_code: int
    sloc: int
    nesting_depth: int
    halstead_volume: float
    halstead_difficulty: float
    halstead_effort: float


class ComplexityEngine:
    OPERATOR_KEYWORDS = {
        "+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "=", "+=", "-=",
        "*=", "/=", "and", "or", "not", "&&", "||", "!", "if", "else", "elif", "for",
        "while", "return", "try", "except", "catch", "finally", "import", "class", "def", "function"
    }

    def compute_file_metrics(self, file_path: str, content: str, ast_nodes: List[ASTNode]) -> CalculatedMetrics:
        lines = content.splitlines()
        loc = len(lines)
        sloc = len([l for l in lines if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("//")])

        # 1. Cyclomatic Complexity
        cyclomatic = 1
        decision_patterns = [
            r"\bif\b", r"\belif\b", r"\bfor\b", r"\bwhile\b", r"\bexcept\b", r"\bcatch\b", r"\bcase\b", r"\band\b", r"\bor\b", r"&&", r"\|\|"
        ]
        for line in lines:
            # Skip pure comments
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            for pat in decision_patterns:
                cyclomatic += len(re.findall(pat, line))

        # 2. Cognitive Complexity & Max Nesting Depth
        cognitive = 0
        max_nesting = 0
        current_indent_stack = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue

            # Calculate indentation level (indent space count // 4)
            indent = len(line) - len(line.lstrip(" "))
            level = indent // 4

            if level > max_nesting:
                max_nesting = level

            if any(re.search(pat, stripped) for pat in [r"\bif\b", r"\bfor\b", r"\bwhile\b"]):
                cognitive += (1 + level)

        # 3. Halstead Metrics
        tokens = re.findall(r"\w+|[^\w\s]", content)
        operators = []
        operands = []

        for tok in tokens:
            if tok in self.OPERATOR_KEYWORDS or not tok.isalnum():
                operators.append(tok)
            else:
                operands.append(tok)

        n1 = len(set(operators))
        n2 = len(set(operands))
        N1 = len(operators)
        N2 = len(operands)

        vocabulary = n1 + n2
        length = N1 + N2

        if vocabulary > 0 and length > 0:
            volume = length * math.log2(vocabulary)
        else:
            volume = 1.0

        difficulty = (n1 / 2.0) * (N2 / max(1, n2))
        effort = difficulty * volume

        # 4. Maintainability Index (MI)
        # MI = 171 - 5.2 * ln(V) - 0.23 * V(G) - 16.2 * ln(LOC)
        raw_mi = 171.0 - (5.2 * math.log(max(1.0, volume))) - (0.23 * cyclomatic) - (16.2 * math.log(max(1, loc)))
        # Normalize MI to 0-100 scale: (raw_mi * 100 / 171)
        normalized_mi = max(0.0, min(100.0, (raw_mi * 100.0) / 171.0))

        return CalculatedMetrics(
            file_path=file_path,
            function_name=None,
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            maintainability_index=round(normalized_mi, 2),
            lines_of_code=loc,
            sloc=sloc,
            nesting_depth=max_nesting,
            halstead_volume=round(volume, 2),
            halstead_difficulty=round(difficulty, 2),
            halstead_effort=round(effort, 2),
        )


complexity_engine = ComplexityEngine()
