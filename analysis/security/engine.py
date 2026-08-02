import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SecurityFindingData:
    file_path: str
    cve_or_rule: str
    vulnerability_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    line_number: int
    evidence_snippet: Optional[str] = None


class SecurityAnalysisEngine:
    ONE_FINDING_PER_FILE_RULES = {
        "DEBUG_ENABLED",
        "DEFAULT_SECRET",
        "INSECURE_CORS",
        "INSECURE_DB_FALLBACK",
        "PLAINTEXT_ENV_SECRET",
    }
    TEST_PATH_PARTS = {"/tests/", "\\tests\\", "/test/", "\\test\\"}

    VULN_PATTERNS = [
        # 1. SQL Injection
        (
            "SQL_INJECTION",
            "SQL Injection",
            "CRITICAL",
            r"(?:execute|query|raw)\s*\(\s*(?:f[\"']|[\"'].*%|\s*\w+\s*\+)",
            "Possible SQL Injection. Query constructed using raw string formatting or concatenation.",
        ),
        (
            "SQL_INJECTION",
            "SQL Injection",
            "CRITICAL",
            r"SELECT\s+.*\s+FROM\s+.*\+\s*\w+",
            "Raw string concatenation in SQL SELECT query.",
        ),

        # 2. Command Injection
        (
            "COMMAND_INJECTION",
            "Command Injection",
            "CRITICAL",
            r"\b(os\.system|os\.popen|os\.execvp)\s*\(",
            "Command Injection risk. Executing system shell command with untrusted input.",
        ),
        (
            "COMMAND_INJECTION",
            "Command Injection",
            "CRITICAL",
            r"\b(subprocess\.call|subprocess\.Popen|subprocess\.run)\s*\(.*shell\s*=\s*True",
            "Command Injection risk. Executing shell command with shell=True and untrusted input.",
        ),
        (
            "COMMAND_INJECTION",
            "Command Injection",
            "CRITICAL",
            r"\b(eval|exec)\s*\(",
            "Dynamic code execution via eval() or exec() poses severe RCE risks.",
        ),

        # 3. Path Traversal
        (
            "PATH_TRAVERSAL",
            "Path Traversal",
            "HIGH",
            r"open\s*\(\s*.*(?:req|input|param|user).*\)",
            "Path Traversal risk. Opening file path derived directly from user input without normalization.",
        ),

        # 4. Weak Randomness
        (
            "WEAK_RANDOM",
            "Weak Cryptographic Randomness",
            "MEDIUM",
            r"\b(random\.random|random\.randint|Math\.random|rand)\b",
            "Use of pseudo-random number generator for security or token generation. Use 'secrets' or 'crypto' module.",
        ),

        # 5. Hardcoded Secret / Password
        (
            "HARDCODED_SECRET",
            "Hardcoded Credentials",
            "HIGH",
            r"(?:password|passwd|api_key|secret_key|secret|token)\s*(?::[^=]+)?=\s*[\"'][^\"']{4,}[\"']",
            "Hardcoded credential or secret key detected in source code.",
        ),
        (
            "DEFAULT_SECRET",
            "Default Secret Key",
            "HIGH",
            r"(?:secret_key|secret|jwt_secret)\s*(?::[^=]+)?=\s*[\"'][^\"']*(?:change[_ -]?this|default|secret[_ -]?key|in[_ -]?production)[^\"']*[\"']",
            "Default or placeholder secret key detected. Replace it with a strong environment-provided secret before deployment.",
        ),

        # 6. Insecure Deserialization
        (
            "INSECURE_DESERIALIZATION",
            "Insecure Deserialization",
            "CRITICAL",
            r"\b(pickle\.loads|pickle\.load|yaml\.unsafe_load|Marshal\.load)\b",
            "Insecure deserialization vulnerability allows arbitrary code execution.",
        ),

        # 7. Cross-Site Scripting (XSS)
        (
            "XSS",
            "Cross-Site Scripting (XSS)",
            "HIGH",
            r"(?:dangerouslySetInnerHTML|innerHTML\s*=|document\.write\s*\()",
            "Unsanitized HTML insertion poses Cross-Site Scripting (XSS) vulnerabilities.",
        ),

        # 8. CSRF / Insecure Configuration
        (
            "CSRF",
            "Insecure CORS / Missing CSRF Protection",
            "MEDIUM",
            r"Access-Control-Allow-Origin['\"]?\s*:\s*['\"]\*['\"]",
            "Wildcard Access-Control-Allow-Origin ('*') exposes APIs to unauthorized cross-origin requests.",
        ),
        (
            "INSECURE_CORS",
            "Insecure CORS Configuration",
            "HIGH",
            r"allow_origins\s*=\s*\[\s*[\"']\*[\"']\s*\]",
            "FastAPI CORS allows every origin. Restrict origins to trusted frontend domains before production.",
        ),
        (
            "DEBUG_ENABLED",
            "Debug Mode Enabled",
            "MEDIUM",
            r"\bdebug\s*(?::[^=]+)?=\s*true\b",
            "Debug mode is enabled by default. Disable debug behavior in deployed environments.",
        ),
        (
            "INSECURE_DB_FALLBACK",
            "Insecure Database Fallback",
            "MEDIUM",
            r"(?:fallback|using local sqlite|sqlite:///|create_all\s*\()",
            "Database fallback or automatic table creation can hide production database failures and bypass migrations.",
        ),
        (
            "PLAINTEXT_ENV_SECRET",
            "Plaintext Secret in Environment File",
            "HIGH",
            r"^(?:[A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API_KEY)[A-Z0-9_]*)\s*=\s*[^\\s#]+",
            "Environment/config file contains a plaintext credential value. Keep only examples/placeholders in committed files.",
        ),

        # 9. Unsafe Reflection
        (
            "UNSAFE_REFLECTION",
            "Unsafe Reflection",
            "HIGH",
            r"\b(getattr|Class\.forName|reflect\.ValueOf)\s*\(\s*.*(?:input|param|user)",
            "Dynamic class/method reflection using untrusted input string.",
        ),

        # 10. Weak Cryptography
        (
            "WEAK_CRYPTOGRAPHY",
            "Weak Cryptographic Hash / Cipher",
            "HIGH",
            r"\b(hashlib\.md5|hashlib\.sha1|Crypto\.Cipher\.DES|RC4)\b",
            "Use of weak or deprecated hash algorithm (MD5/SHA1) or cipher (DES/RC4). Upgrade to SHA-256 or AES-GCM.",
        ),

        # 11. Unsafe File Access
        (
            "UNSAFE_FILE_ACCESS",
            "Insecure File Operation",
            "MEDIUM",
            r"\b(tempfile\.mktemp|tmpnam)\b",
            "Insecure temporary file creation vulnerability. Use tempfile.NamedTemporaryFile instead.",
        ),

        # 12. Secret Exposure in Logs
        (
            "SECRET_EXPOSURE",
            "Sensitive Data Exposure in Logging",
            "MEDIUM",
            r"\b(print|logger\.info|console\.log)\s*\(\s*.*(?:password|token|secret|credit_card)",
            "Sensitive credential or token logged to standard output or log file.",
        ),

        # 13. Unsafe API Calls (C/C++)
        (
            "UNSAFE_API",
            "Insecure C Standard Library API",
            "HIGH",
            r"\b(strcpy|gets|sprintf)\s*\(",
            "Use of unsafe memory API (strcpy/gets/sprintf) susceptible to buffer overflows. Use strncpy/fgets/snprintf.",
        ),
    ]

    def scan_file(self, file_path: str, content: str) -> List[SecurityFindingData]:
        findings: List[SecurityFindingData] = []
        lines = content.splitlines()
        emitted_file_rules: set[str] = set()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            for rule_id, vtype, severity, pattern, desc in self.VULN_PATTERNS:
                if rule_id in emitted_file_rules:
                    continue
                if rule_id == "INSECURE_DB_FALLBACK" and self._is_test_path(file_path):
                    continue
                if stripped.startswith("#") or stripped.startswith("//"):
                    if rule_id != "PLAINTEXT_ENV_SECRET":
                        continue
                if rule_id == "PLAINTEXT_ENV_SECRET":
                    matched = re.search(pattern, stripped) is not None
                else:
                    matched = re.search(pattern, stripped, re.IGNORECASE) is not None

                if matched:
                    if rule_id in self.ONE_FINDING_PER_FILE_RULES:
                        emitted_file_rules.add(rule_id)
                    findings.append(
                        SecurityFindingData(
                            file_path=file_path,
                            cve_or_rule=rule_id,
                            vulnerability_type=vtype,
                            severity=severity,
                            description=desc,
                            line_number=idx,
                            evidence_snippet=stripped,
                        )
                    )

        return findings

    def _is_test_path(self, file_path: str) -> bool:
        normalized = file_path.replace("\\", "/").lower()
        return "/tests/" in normalized or "/test/" in normalized or normalized.startswith("tests/")


security_analysis_engine = SecurityAnalysisEngine()
