from mcp.server.fastmcp import FastMCP
from pathlib import Path
import zipfile
import uuid
import base64
import shutil
import atexit

# -------------------------------------------------
# MCP APP
# -------------------------------------------------
mcp = FastMCP("zip-workspace-cloud")

# -------------------------------------------------
# CLOUD-SAFE STORAGE (EPHEMERAL)
# -------------------------------------------------
BASE_DIR = Path("/tmp/workspaces")
BASE_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# HARD CONSTRAINTS
# -------------------------------------------------
MAX_FILES = 10_000
MAX_TOTAL_SIZE_MB = 500
MAX_TOTAL_SIZE_BYTES = MAX_TOTAL_SIZE_MB * 1024 * 1024
MAX_FILE_READ_BYTES = 300_000  # per-file LLM safety

# Track workspaces for cleanup (per Claude session)
ACTIVE_WORKSPACES: set[str] = set()

# -------------------------------------------------
# CLEANUP ON SESSION END
# -------------------------------------------------
def cleanup_all():
    for wid in ACTIVE_WORKSPACES:
        path = BASE_DIR / wid
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    ACTIVE_WORKSPACES.clear()

atexit.register(cleanup_all)

# -------------------------------------------------
# ZIP EXTRACTION CORE
# -------------------------------------------------
def extract_zip_bytes(zip_bytes: bytes) -> str:
    if len(zip_bytes) > MAX_TOTAL_SIZE_BYTES:
        raise ValueError("ZIP exceeds 500 MB limit")

    workspace_id = str(uuid.uuid4())
    workspace_dir = BASE_DIR / workspace_id
    workspace_dir.mkdir(parents=True, exist_ok=True)
    ACTIVE_WORKSPACES.add(workspace_id)

    zip_path = workspace_dir / "upload.zip"
    zip_path.write_bytes(zip_bytes)

    total_size = 0
    file_count = 0

    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if info.is_dir():
                continue

            file_count += 1
            total_size += info.file_size

            if file_count > MAX_FILES:
                raise ValueError("ZIP contains more than 10,000 files")

            if total_size > MAX_TOTAL_SIZE_BYTES:
                raise ValueError("Extracted data exceeds 500 MB")

            extracted_path = (workspace_dir / info.filename).resolve()

            # ZIP SLIP PROTECTION
            if workspace_dir.resolve() not in extracted_path.parents:
                raise ValueError("Unsafe ZIP path detected")

            extracted_path.parent.mkdir(parents=True, exist_ok=True)
            z.extract(info, workspace_dir)

    return workspace_id

# -------------------------------------------------
# MCP TOOLS
# -------------------------------------------------

@mcp.tool()
def upload_zip_base64(zip_base64: str) -> str:
    """
    Upload a ZIP file (base64 encoded).

    Constraints:
    - Max files: 10,000
    - Max size: 500 MB
    - Auto-deleted after Claude session ends
    """
    zip_bytes = base64.b64decode(zip_base64)
    return extract_zip_bytes(zip_bytes)


@mcp.tool()
def list_files(workspace_id: str) -> list[str]:
    root = (BASE_DIR / workspace_id).resolve()
    if not root.exists():
        return []

    return [
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file()
    ]


@mcp.tool()
def read_file(workspace_id: str, path: str) -> str:
    root = (BASE_DIR / workspace_id).resolve()
    file_path = (root / path).resolve()

    if root not in file_path.parents:
        raise ValueError("Invalid path")

    if not file_path.exists():
        raise ValueError("File not found")

    if file_path.stat().st_size > MAX_FILE_READ_BYTES:
        raise ValueError("File too large to read")

    return file_path.read_text(errors="ignore")


@mcp.tool()
def search_text(workspace_id: str, query: str) -> list[str]:
    root = (BASE_DIR / workspace_id).resolve()
    if not root.exists():
        return []

    matches = []
    for file in root.rglob("*"):
        if file.is_file() and file.stat().st_size <= MAX_FILE_READ_BYTES:
            try:
                if query in file.read_text(errors="ignore"):
                    matches.append(str(file.relative_to(root)))
            except:
                pass
    return matches

# -------------------------------------------------
# MCP ENTRYPOINT
# -------------------------------------------------
if __name__ == "__main__":
    mcp.run()
