from fastapi import FastAPI, UploadFile, File
from pathlib import Path
from workspace import extract_zip

app = FastAPI()

PROJECT_ROOT = Path(__file__).resolve().parent
TEMP_ZIP = PROJECT_ROOT / "temp.zip"


@app.post("/upload-zip")
async def upload_zip(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        return {"error": "Only ZIP files allowed"}

    TEMP_ZIP.write_bytes(await file.read())

    workspace_id = extract_zip(TEMP_ZIP)
    TEMP_ZIP.unlink(missing_ok=True)

    return {
        "workspace_id": workspace_id,
        "workspace_path": str((PROJECT_ROOT / "workspaces" / workspace_id).resolve())
    }
