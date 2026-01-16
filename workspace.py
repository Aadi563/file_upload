import zipfile
import uuid
from pathlib import Path

# ABSOLUTE project root
PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = PROJECT_ROOT / "workspaces"
BASE_DIR.mkdir(exist_ok=True)

MAX_FILES = 10000
MAX_SIZE_MB = 1000


def extract_zip(zip_path: Path) -> str:
    workspace_id = str(uuid.uuid4())
    target = BASE_DIR / workspace_id
    target.mkdir(parents=True, exist_ok=True)

    total_size = 0
    file_count = 0

    with zipfile.ZipFile(zip_path) as z:
        print("ZIP CONTENTS:", z.namelist())

        for info in z.infolist():
            if info.is_dir():
                continue

            file_count += 1
            total_size += info.file_size

            if file_count > MAX_FILES:
                raise ValueError("Too many files in ZIP")

            if total_size > MAX_SIZE_MB * 1024 * 1024:
                raise ValueError("ZIP too large")

            extracted_path = (target / info.filename).resolve()

            # ZIP SLIP PROTECTION (Windows-safe)
            if target.resolve() not in extracted_path.parents:
                raise ValueError("Unsafe ZIP path detected")

            extracted_path.parent.mkdir(parents=True, exist_ok=True)
            z.extract(info, target)

    print("EXTRACTED TO:", target)
    return workspace_id
