import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from analysis.parsers.base import ASTNode


@dataclass
class StaticFindingData:
    file_path: str
    rule_id: str
    category: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    line_start: int
    line_end: int
    col_start: Optional[int] = None
    col_end: Optional[int] = None
    evidence_snippet: Optional[str] = None


class StaticAnalysisEngine:
    def analyze_file(self, file_path: str, content: str, ast_nodes: List[ASTNode]) -> List[StaticFindingData]:
        findings: List[StaticFindingData] = []
        lines = content.splitlines()

        # 1. Check Long Methods (> 30 lines in function)
        in_func = False
        func_start_line = 0
        func_name = ""

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Function start check
            func_match = re.search(r"def\s+(\w+)\s*\(|function\s+(\w+)\s*\(", stripped)
            if func_match:
                if in_func:
                    func_length = (idx - 1) - func_start_line + 1
                    if func_length > 30:
                        findings.append(
                            StaticFindingData(
                                file_path=file_path,
                                rule_id="LONG_METHOD",
                                category="Maintainability",
                                severity="MEDIUM",
                                message=f"Function '{func_name}' is too long ({func_length} lines). Consider refactoring into smaller helper functions.",
                                line_start=func_start_line,
                                line_end=idx - 1,
                                evidence_snippet=lines[func_start_line - 1] if func_start_line <= len(lines) else "",
                            )
                        )
                in_func = True
                func_start_line = idx
                func_name = func_match.group(1) or func_match.group(2) or "anonymous"

        if in_func and (len(lines) - func_start_line + 1) > 30:
            findings.append(
                StaticFindingData(
                    file_path=file_path,
                    rule_id="LONG_METHOD",
                    category="Maintainability",
                    severity="MEDIUM",
                    message=f"Function '{func_name}' is too long ({len(lines) - func_start_line + 1} lines). Consider refactoring into smaller helper functions.",
                    line_start=func_start_line,
                    line_end=len(lines),
                    evidence_snippet=lines[func_start_line - 1],
                )
            )

        # 2. Check Deep Nesting (> 3 levels / 12 spaces)
        for idx, line in enumerate(lines, start=1):
            if not line.strip() or line.strip().startswith("#") or line.strip().startswith("//"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            if indent >= 16:  # 4 levels of nesting
                findings.append(
                    StaticFindingData(
                        file_path=file_path,
                        rule_id="DEEP_NESTING",
                        category="Complexity",
                        severity="MEDIUM",
                        message=f"Excessive nesting depth detected ({indent // 4} levels). Deep nesting increases cognitive load.",
                        line_start=idx,
                        line_end=idx,
                        evidence_snippet=line.strip(),
                    )
                )

        # 3. Check Dead Code (code after return/raise/break in same block)
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped in ["return", "break", "continue", "raise Exception()"] or stripped.startswith("return "):
                if idx < len(lines):
                    next_line = lines[idx].strip()
                    if next_line and not next_line.startswith("def ") and not next_line.startswith("class ") and not next_line.startswith("#") and not next_line.startswith("}"):
                        # Check indentation to ensure it's in the same block
                        next_indent = len(lines[idx]) - len(lines[idx].lstrip(" "))
                        curr_indent = len(line) - len(line.lstrip(" "))
                        if next_indent == curr_indent:
                            findings.append(
                                StaticFindingData(
                                    file_path=file_path,
                                    rule_id="DEAD_CODE",
                                    category="Correctness",
                                    severity="HIGH",
                                    message="Unreachable dead code detected following unconditional return/break statement.",
                                    line_start=idx + 1,
                                    line_end=idx + 1,
                                    evidence_snippet=next_line,
                                )
                            )

        # 4. Check Magic Numbers
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            # Look for comparisons with numbers != 0, 1, -1, 2
            magic_matches = re.findall(r"(?:==|>|<|>=|<=|\+|\*)\s*([3-9]\d*|\d{2,})", stripped)
            if magic_matches:
                for num in magic_matches:
                    findings.append(
                        StaticFindingData(
                            file_path=file_path,
                            rule_id="MAGIC_NUMBER",
                            category="Style",
                            severity="LOW",
                            message=f"Magic number '{num}' hardcoded in expression. Define as a named constant for clarity.",
                            line_start=idx,
                            line_end=idx,
                            evidence_snippet=stripped,
                        )
                    )

        # 5. Check Poor Naming (single-letter variables except i, j, k, n, x, y in math contexts)
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            # Single letter variable assignments like `a = 10` or `b = calc()`
            poor_var_matches = re.findall(r"\b([a-hj-mop-wzA-Z])\s*=\s*", stripped)
            if poor_var_matches:
                for var in poor_var_matches:
                    findings.append(
                        StaticFindingData(
                            file_path=file_path,
                            rule_id="POOR_NAMING",
                            category="Style",
                            severity="LOW",
                            message=f"Non-descriptive single-letter variable name '{var}'. Use self-documenting identifiers.",
                            line_start=idx,
                            line_end=idx,
                            evidence_snippet=stripped,
                        )
                    )

        return findings


static_analysis_engine = StaticAnalysisEngine()
