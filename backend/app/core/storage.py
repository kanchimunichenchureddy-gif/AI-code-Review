import os
import hashlib
import io
import zipfile
from pathlib import Path
from typing import List, Dict, Tuple


BASE_STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage")).resolve()
MAX_EXTRACTED_FILES = 500
MAX_EXTRACTED_TOTAL_BYTES = 10_000_000
MAX_EXTRACTED_SINGLE_FILE_BYTES = 1_000_000
IGNORED_ARCHIVE_SEGMENTS = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".nuxt",
    ".cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "target",
    ".venv",
    "venv",
    "env",
}


class StorageSecurityError(Exception):
    pass


class StorageManager:
    def __init__(self, base_dir: Path = BASE_STORAGE_DIR):
        self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_submission_dir(self, assignment_id: int, student_id: int, submission_id: int) -> Path:
        sub_dir = self.base_dir / "submissions" / str(assignment_id) / str(student_id) / str(submission_id)
        sub_dir = sub_dir.resolve()
        # Verify path safety against traversal attacks
        if not str(sub_dir).startswith(str(self.base_dir)):
            raise StorageSecurityError("Path traversal attempt detected")
        sub_dir.mkdir(parents=True, exist_ok=True)
        return sub_dir

    def compute_file_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def save_file(self, target_dir: Path, filename: str, content: str) -> Tuple[Path, str]:
        # Path traversal security check
        normalized_filename = filename.replace("\\", "/").strip("/")
        filename_parts = Path(normalized_filename).parts
        if (
            not normalized_filename
            or ".." in filename_parts
            or filename.startswith("/")
            or filename.startswith("\\")
        ):
            raise StorageSecurityError(f"Directory traversal sequence detected in filename: {filename}")

        target_path = (target_dir / normalized_filename).resolve()

        if not str(target_path).startswith(str(target_dir.resolve())):
            raise StorageSecurityError(f"Directory traversal detected in filename: {filename}")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        file_hash = self.compute_file_hash(content)
        return target_path, file_hash

    def extract_zip_bytes(self, zip_content: bytes, allowed_extensions: List[str]) -> List[Dict[str, str]]:
        extracted_files = []
        total_uncompressed_bytes = 0
        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zf:
            for zip_info in zf.infolist():
                if len(extracted_files) >= MAX_EXTRACTED_FILES:
                    break
                if zip_info.is_dir():
                    continue

                # Skip path traversal, hidden files, or __MACOSX
                if ".." in zip_info.filename or zip_info.filename.startswith("__MACOSX") or "/." in zip_info.filename or zip_info.filename.startswith("."):
                    continue
                if any(part in IGNORED_ARCHIVE_SEGMENTS for part in Path(zip_info.filename).parts):
                    continue

                # Extension check
                ext = os.path.splitext(zip_info.filename)[1].lower()
                if allowed_extensions and ext not in allowed_extensions:
                    continue
                if zip_info.file_size > MAX_EXTRACTED_SINGLE_FILE_BYTES:
                    continue
                if total_uncompressed_bytes + zip_info.file_size > MAX_EXTRACTED_TOTAL_BYTES:
                    break

                # Read text content safely
                with zf.open(zip_info) as f:
                    try:
                        file_text = f.read().decode("utf-8", errors="replace")
                        total_uncompressed_bytes += len(file_text.encode("utf-8"))
                        extracted_files.append({
                            "filename": zip_info.filename.strip("/"),
                            "content": file_text
                        })
                    except Exception:
                        continue

        return extracted_files


storage_manager = StorageManager()
