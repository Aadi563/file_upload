from mcp.server.fastmcp import FastMCP
from pathlib import Path
import os

# ABSOLUTE paths
PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = PROJECT_ROOT / "workspaces"

print("=== MCP SERVER STARTED ===")
print("SERVER FILE:", __file__)
print("PROJECT ROOT:", PROJECT_ROOT)
print("WORKSPACES DIR EXISTS:", BASE_DIR.exists())
print("WORKSPACES CONTENT:", list(BASE_DIR.iterdir()) if BASE_DIR.exists() else [])

mcp = FastMCP("zip-workspace")


@mcp.tool()
def debug_info() -> dict:
    return {
        "server_file": __file__,
        "cwd": os.getcwd(),
        "project_root": str(PROJECT_ROOT),
        "workspaces": [p.name for p in BASE_DIR.iterdir()] if BASE_DIR.exists() else []
    }


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

    if file_path.stat().st_size > 200_000:
        raise ValueError("File too large")

    return file_path.read_text(errors="ignore")


@mcp.tool()
def search_text(workspace_id: str, query: str) -> list[str]:
    root = (BASE_DIR / workspace_id).resolve()
    matches = []

    if not root.exists():
        return matc
