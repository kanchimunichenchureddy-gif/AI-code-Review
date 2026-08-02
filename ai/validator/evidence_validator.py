from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from backend.app.models.submission import SubmissionFile
from backend.app.models.finding import StaticFindingModel, SecurityFindingModel


@dataclass
class FeedbackCandidate:
    category: str
    title: str
    what_text: str
    why_text: str
    how_to_fix_text: str
    example_code: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]


class EvidenceValidator:
    def validate_candidate(
        self,
        candidate: FeedbackCandidate,
        files: List[SubmissionFile],
        static_findings: List[StaticFindingModel],
        security_findings: List[SecurityFindingModel],
    ) -> bool:
        # General non-line feedback (e.g. Overall Praise/Summary) is allowed if category is Strengths/Summary
        if not candidate.file_path and candidate.category in ["Strengths", "Overall Summary", "General Advice"]:
            return True

        # File path must exist in submission
        file_map = {f.filename: f for f in files}
        if candidate.file_path and candidate.file_path not in file_map:
            return False  # Hallucinated file path

        target_file = file_map.get(candidate.file_path)

        # Line number must be valid within file boundaries
        if candidate.line_number is not None and target_file:
            line_count = len(target_file.content.splitlines())
            if candidate.line_number < 1 or candidate.line_number > max(1, line_count):
                return False  # Hallucinated line number outside bounds

        # Ground truth evidence check: Must match a deterministic static or security finding
        has_matching_static = any(
            sf.file_path == candidate.file_path and
            (candidate.line_number is None or sf.line_start <= candidate.line_number <= sf.line_end)
            for sf in static_findings
        )

        has_matching_security = any(
            sec.file_path == candidate.file_path and
            (candidate.line_number is None or sec.line_number == candidate.line_number)
            for sec in security_findings
        )

        return has_matching_static or has_matching_security


evidence_validator = EvidenceValidator()
