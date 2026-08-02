from typing import List, Dict, Any
from sqlalchemy.orm import Session

from ai.validator.evidence_validator import evidence_validator, FeedbackCandidate
from backend.app.models.submission import Submission
from backend.app.models.finding import (
    StaticFindingModel,
    SecurityFindingModel,
    ComplexityMetricModel,
    FeedbackModel,
)


class AIFeedbackService:
    # Pedagogical knowledge base mapping rule IDs to 4-part educational explanations
    PEDAGOGICAL_KNOWLEDGE_BASE = {
        "SQL_INJECTION": {
            "title": "Prevent SQL Injection with Parameterized Queries",
            "what": "Raw string concatenation or string formatting was used to assemble a database query.",
            "why": "Unsanitized user inputs concatenated into SQL statements allow attackers to inject malicious SQL commands, bypass authentication, and manipulate database contents.",
            "how_to_fix": "Use parameterized queries or ORM placeholders (e.g., cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))) to separate SQL logic from data input.",
            "example_code": "# Good / Secure Implementation:\ncursor.execute('SELECT * FROM users WHERE username = %s', (username,))",
            "learning_resource": "Review OWASP guidance on injection prevention and parameterized database queries.",
        },
        "COMMAND_INJECTION": {
            "title": "Avoid Unsafe Shell Command Execution",
            "what": "Shell execution functions (e.g. os.system or shell=True) were called with unsanitized arguments.",
            "why": "Passing untrusted inputs to system shells allows command injection, permitting attackers to execute arbitrary binary commands on the host server.",
            "how_to_fix": "Use subprocess.run with argument lists and shell=False instead of raw string shell invocation.",
            "example_code": "# Good / Secure Implementation:\nimport subprocess\nsubprocess.run(['ls', '-l', filename], check=True, shell=False)",
            "learning_resource": "Study secure subprocess usage and command injection prevention patterns.",
        },
        "DEAD_CODE": {
            "title": "Remove Unreachable Dead Code",
            "what": "Statements were found after an unconditional return, raise, or break statement.",
            "why": "Unreachable code can never be executed, confusing maintainers and cluttering the codebase.",
            "how_to_fix": "Delete unreachable statements or restructure conditional branches so all code paths execute intentionally.",
            "example_code": "# Good Implementation:\ndef process(data):\n    # Perform cleanup prior to returning\n    cleanup()\n    return data",
            "learning_resource": "Practice tracing control flow and identifying unreachable branches.",
        },
        "DEEP_NESTING": {
            "title": "Refactor Deeply Nested Code Blocks",
            "what": "Code block nesting depth exceeds 3 levels.",
            "why": "Deeply nested loops and conditionals increase cognitive complexity, making code harder to read, debug, and test.",
            "how_to_fix": "Apply Guard Clauses (early returns) or extract inner nested logic into dedicated helper functions.",
            "example_code": "# Good (Guard Clause) Implementation:\ndef process(item):\n    if not item:\n        return\n    if not item.is_valid():\n        return\n    do_work(item)",
            "learning_resource": "Review guard clauses, function extraction, and cognitive complexity basics.",
        },
        "MAGIC_NUMBER": {
            "title": "Replace Magic Numbers with Named Constants",
            "what": "Hardcoded numeric literals were detected directly inside conditional or arithmetic logic.",
            "why": "Magic numbers obscure business intent and require manual updates across multiple code locations when values change.",
            "how_to_fix": "Define self-documenting module-level constants (e.g. SECONDS_PER_DAY = 86400).",
            "example_code": "# Good Implementation:\nSECONDS_PER_DAY = 86400\nif elapsed_time > SECONDS_PER_DAY:\n    reset_session()",
            "learning_resource": "Review named constants and self-documenting code conventions.",
        },
        "POOR_NAMING": {
            "title": "Use Descriptive, Self-Documenting Variable Names",
            "what": "Cryptic single-letter variable names were detected.",
            "why": "Single-letter variable names force readers to scan surrounding code to understand variable purpose.",
            "how_to_fix": "Use descriptive identifiers that convey domain meaning (e.g. user_account_balance instead of a).",
            "example_code": "# Good Implementation:\nuser_account_balance = fetch_balance()",
            "learning_resource": "Review naming conventions for the submission language and prefer domain-specific names.",
        },
        "HARDCODED_SECRET": {
            "title": "Externalize Plaintext Secrets and Passwords",
            "what": "Hardcoded credentials or API keys were detected in source code.",
            "why": "Committing credentials to source code repositories risks credential leak and unauthorized access.",
            "how_to_fix": "Load credentials dynamically from environment variables or secure secret managers.",
            "example_code": "# Good Implementation:\nimport os\napi_key = os.getenv('API_KEY')",
            "learning_resource": "Review secret-management basics and environment-variable configuration.",
        },
        "DEFAULT_SECRET": {
            "title": "Replace Default Secret Keys",
            "what": "A default or placeholder application secret was detected.",
            "why": "Predictable JWT or session secrets allow attackers to forge tokens or impersonate users.",
            "how_to_fix": "Require a strong SECRET_KEY from the deployment environment and fail startup when it is missing.",
            "example_code": "SECRET_KEY = os.environ['SECRET_KEY']",
            "learning_resource": "Review secure configuration and secret rotation practices.",
        },
        "INSECURE_CORS": {
            "title": "Restrict CORS Origins",
            "what": "The API allows requests from every browser origin.",
            "why": "Wildcard CORS can expose authenticated APIs to untrusted websites when credentials or browser sessions are involved.",
            "how_to_fix": "Replace '*' with a configured allow-list of trusted frontend URLs for each environment.",
            "example_code": "allow_origins=settings.CORS_ALLOWED_ORIGINS",
            "learning_resource": "Review browser same-origin policy and CORS allow-list configuration.",
        },
        "DEBUG_ENABLED": {
            "title": "Disable Debug Mode by Default",
            "what": "Debug mode is enabled in configuration.",
            "why": "Debug behavior can expose stack traces, internals, and unsafe development behavior in deployed systems.",
            "how_to_fix": "Default DEBUG to false and enable it only in local development environments.",
            "example_code": "DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'",
            "learning_resource": "Review twelve-factor app configuration practices.",
        },
        "INSECURE_DB_FALLBACK": {
            "title": "Avoid Silent Database Fallbacks",
            "what": "The app can silently fall back to a local database or auto-create tables.",
            "why": "Silent fallback hides production outages and can make the app run against the wrong data store.",
            "how_to_fix": "Fail fast when the configured production database is unavailable and use migrations for schema changes.",
            "example_code": "engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)",
            "learning_resource": "Review production database migration and fail-fast startup patterns.",
        },
        "PLAINTEXT_ENV_SECRET": {
            "title": "Remove Plaintext Secrets From Config Files",
            "what": "A committed environment/config line appears to contain a plaintext credential.",
            "why": "Credentials in repository files are easy to leak and hard to rotate after exposure.",
            "how_to_fix": "Keep only placeholder examples in committed files and load real values from a secret manager or local .env excluded by git.",
            "example_code": "MYSQL_PASSWORD=<set-in-local-env-not-committed>",
            "learning_resource": "Review secret scanning and environment file hygiene.",
        },
    }

    def generate_feedback_for_submission(self, db: Session, submission: Submission) -> List[FeedbackModel]:
        # Delete existing feedback for this submission
        db.query(FeedbackModel).filter(FeedbackModel.submission_id == submission.id).delete()
        db.flush()

        candidates: List[FeedbackCandidate] = []

        # 1. Add Positive Feedback Candidate if maintainability is high
        for m in submission.complexity_metrics:
            if m.maintainability_index >= 70.0:
                candidates.append(
                    FeedbackCandidate(
                        category="Strengths",
                        title="Excellent Code Maintainability",
                        what_text=f"File '{m.file_path}' achieved a high Maintainability Index of {m.maintainability_index}/100.",
                        why_text="Well-structured code with manageable complexity is easier to test, debug, and maintain over time.",
                        how_to_fix_text="Continue preserving modular function design and clear variable naming. Learning resource: review maintainability metrics and small-function design.",
                        example_code=None,
                        file_path=None,
                        line_number=None,
                    )
                )

        # 2. Process Security Findings into 4-part Educational Feedback
        for sec in submission.security_findings:
            kb = self.PEDAGOGICAL_KNOWLEDGE_BASE.get(sec.cve_or_rule, {
                "title": f"Security Notice: {sec.vulnerability_type}",
                "what": sec.description,
                "why": "Security vulnerabilities in student submissions expose software to potential exploits.",
                "how_to_fix": "Review secure coding guidelines for input validation and sanitization.",
                "example_code": None,
                "learning_resource": "Review OWASP secure coding practices for this vulnerability category.",
            })

            candidates.append(
                FeedbackCandidate(
                    category="Security",
                    title=kb["title"],
                    what_text=f"{kb['what']} (Detected at line {sec.line_number})",
                    why_text=kb["why"],
                    how_to_fix_text=self._with_learning_resource(kb),
                    example_code=kb.get("example_code"),
                    file_path=sec.file_path,
                    line_number=sec.line_number,
                )
            )

        # 3. Process Static Findings into 4-part Educational Feedback
        for sf in submission.findings:
            kb = self.PEDAGOGICAL_KNOWLEDGE_BASE.get(sf.rule_id, {
                "title": f"Code Quality Tip: {sf.rule_id}",
                "what": sf.message,
                "why": "Adhering to software engineering best practices improves code readability and maintainability.",
                "how_to_fix": "Refactor code to follow standard style conventions.",
                "example_code": None,
                "learning_resource": "Review clean-code basics for naming, structure, comments, and small functions.",
            })

            candidates.append(
                FeedbackCandidate(
                    category=sf.category,
                    title=kb["title"],
                    what_text=f"{sf.message} {kb['what']} (Line {sf.line_start})",
                    why_text=kb["why"],
                    how_to_fix_text=self._with_learning_resource(kb),
                    example_code=kb.get("example_code"),
                    file_path=sf.file_path,
                    line_number=sf.line_start,
                )
            )

        # 4. Evidence Validation Phase: Discard any invalid or hallucinated candidate
        approved_feedback: List[FeedbackModel] = []
        for cand in candidates:
            is_valid = evidence_validator.validate_candidate(
                candidate=cand,
                files=submission.files,
                static_findings=submission.findings,
                security_findings=submission.security_findings,
            )

            if is_valid:
                fb_model = FeedbackModel(
                    submission_id=submission.id,
                    category=cand.category,
                    title=cand.title,
                    what_text=cand.what_text,
                    why_text=cand.why_text,
                    how_to_fix_text=cand.how_to_fix_text,
                    example_code=cand.example_code,
                    file_path=cand.file_path,
                    line_number=cand.line_number,
                )
                db.add(fb_model)
                approved_feedback.append(fb_model)

        db.commit()
        return approved_feedback

    def _with_learning_resource(self, kb: Dict[str, Any]) -> str:
        resource = kb.get("learning_resource")
        if not resource:
            return kb["how_to_fix"]
        return f"{kb['how_to_fix']} Learning resource: {resource}"


ai_feedback_service = AIFeedbackService()
