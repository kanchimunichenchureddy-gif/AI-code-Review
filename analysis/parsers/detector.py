import os
import re
from typing import Optional


class LanguageDetector:
    # Extension mapping
    EXT_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "javascript",
        ".tsx": "javascript",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".h": "c",
        ".cs": "csharp",
    }

    # Keyword fingerprints
    KEYWORD_PATTERNS = [
        ("python", [r"def\s+\w+\s*\(", r"import\s+\w+", r"from\s+\w+\s+import", r"elif\s+.*:"]),
        ("java", [r"public\s+class\s+\w+", r"import\s+java\.", r"System\.out\.println"]),
        ("javascript", [r"function\s+\w+\s*\(", r"const\s+\w+\s*=", r"let\s+\w+\s*=", r"console\.log"]),
        ("cpp", [r"#include\s+<iostream>", r"std::cout", r"using\s+namespace\s+std", r"template\s*<", r"class\s+\w+"]),
        ("c", [r"#include\s+<stdio.h>", r"#include\s+<stdlib.h>", r"int\s+main\s*\("]),
        ("csharp", [r"using\s+System;", r"namespace\s+\w+", r"Console\.WriteLine"]),
    ]

    def detect_language(self, filename: str, content: str = "") -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.EXT_MAP:
            # Special case for .h: check if C++ keywords exist in content
            if ext == ".h" and content:
                if (
                    re.search(r"class\s+\w+", content)
                    or "std::" in content
                    or "template<" in content
                    or "iostream" in content
                    or "using namespace std" in content
                ):
                    return "cpp"
            return self.EXT_MAP[ext]

        if not content:
            return "unknown"

        # Check content keywords
        for lang, patterns in self.KEYWORD_PATTERNS:
            for pat in patterns:
                if re.search(pat, content):
                    return lang

        return "unknown"


language_detector = LanguageDetector()
