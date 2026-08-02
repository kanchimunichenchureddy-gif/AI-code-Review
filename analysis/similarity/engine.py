import re
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Any
from analysis.parsers.base import ASTNode


@dataclass
class SimilarityComparisonResult:
    similarity_score: float  # Percentage 0.0 to 100.0
    token_similarity: float
    ast_similarity: float
    tier: str  # LOW, MEDIUM, HIGH, Requires Human Review
    human_review_recommended: bool
    matching_regions: List[Dict[str, Any]]


class SimilarityEngine:
    def __init__(self, k_gram_size: int = 5, window_size: int = 4):
        self.k = k_gram_size
        self.w = window_size

    def normalize_code(self, code: str) -> str:
        # Strip comments
        lines = [line for line in code.splitlines() if not line.strip().startswith("#") and not line.strip().startswith("//")]
        clean_code = "\n".join(lines)

        # Extract identifiers in order of appearance (positional ordering)
        identifiers = re.findall(r"\b[a-zA-Z_]\w*\b", clean_code)
        keywords = {
            "def", "class", "return", "if", "else", "elif", "for", "while", "import", "from",
            "in", "is", "not", "and", "or", "try", "except", "public", "private", "static",
            "void", "int", "float", "double", "string", "const", "let", "var", "function", "range", "len"
        }
        
        user_ids = []
        for i in identifiers:
            if i not in keywords and i not in user_ids:
                user_ids.append(i)

        id_map = {uid: f"VAR_{idx}" for idx, uid in enumerate(user_ids)}

        # Substitute user identifiers using word boundary replacement
        normalized = clean_code
        for uid, token in id_map.items():
            normalized = re.sub(r"\b" + re.escape(uid) + r"\b", token, normalized)

        return normalized

    def get_fingerprints(self, text: str) -> Set[str]:
        # Remove whitespace
        compact_text = "".join(text.split())
        if len(compact_text) < self.k:
            return {hashlib.md5(compact_text.encode()).hexdigest()}

        # Generate k-grams
        k_grams = [compact_text[i:i + self.k] for i in range(len(compact_text) - self.k + 1)]
        hashes = [hashlib.md5(gram.encode()).hexdigest() for gram in k_grams]

        # Winnowing algorithm: select min hash per window w
        fingerprints = set()
        if len(hashes) <= self.w:
            fingerprints.add(min(hashes))
        else:
            for i in range(len(hashes) - self.w + 1):
                window = hashes[i:i + self.w]
                fingerprints.add(min(window))

        return fingerprints

    def compute_jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

    def compare_submissions(
        self, code1: str, code2: str, ast_nodes1: List[ASTNode] = None, ast_nodes2: List[ASTNode] = None
    ) -> SimilarityComparisonResult:
        if not code1 or not code2:
            return SimilarityComparisonResult(
                similarity_score=0.0,
                token_similarity=0.0,
                ast_similarity=0.0,
                tier="LOW",
                human_review_recommended=False,
                matching_regions=[],
            )

        # 1. Token Winnowing Similarity
        norm1 = self.normalize_code(code1)
        norm2 = self.normalize_code(code2)

        fp1 = self.get_fingerprints(norm1)
        fp2 = self.get_fingerprints(norm2)

        token_sim = self.compute_jaccard_similarity(fp1, fp2)

        # 2. AST Structure Similarity
        ast_sim = 0.0
        if ast_nodes1 and ast_nodes2:
            ast_types1 = set(n.node_type for n in ast_nodes1)
            ast_types2 = set(n.node_type for n in ast_nodes2)
            ast_sim = self.compute_jaccard_similarity(ast_types1, ast_types2)
        else:
            ast_sim = token_sim  # Fallback to token similarity

        # Combined Weighted Similarity Score
        combined_sim = (token_sim * 0.6) + (ast_sim * 0.4)
        similarity_score = round(combined_sim * 100.0, 2)

        # Classify Risk Tier
        if similarity_score <= 25.0:
            tier = "LOW"
            human_review = False
        elif similarity_score <= 50.0:
            tier = "MEDIUM"
            human_review = False
        elif similarity_score <= 75.0:
            tier = "HIGH"
            human_review = True
        else:
            tier = "Requires Human Review"
            human_review = True

        matching_regions = []
        if similarity_score > 25.0:
            matching_regions.append({
                "type": "AST_FINGERPRINT_MATCH",
                "shared_fingerprints_count": len(fp1.intersection(fp2)),
                "similarity_percentage": similarity_score,
            })

        return SimilarityComparisonResult(
            similarity_score=similarity_score,
            token_similarity=round(token_sim * 100.0, 2),
            ast_similarity=round(ast_sim * 100.0, 2),
            tier=tier,
            human_review_recommended=human_review,
            matching_regions=matching_regions,
        )


similarity_engine = SimilarityEngine()
