import os
import shutil
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.database import get_db
from app.models import FileInfo
from app.auth import verify_api_key, verify_admin_key

router = APIRouter(tags=["files"])

# 文件存储根目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _ensure_upload_dir(task_id: str) -> str:
    path = os.path.join(UPLOAD_DIR, task_id)
    os.makedirs(path, exist_ok=True)
    return path


@router.post("/{task_id}/files", response_model=FileInfo)
def upload_file(
    task_id: str,
    file_type: str = Form(..., description="文件类型: id_card_front / id_card_back / address_proof / other"),
    file: UploadFile = File(..., description="文件内容"),
    _=Depends(verify_admin_key),
):
    # 验证任务存在
    with get_db() as db:
        row = db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

    # 验证文件类型
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，支持: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 验证文件大小
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件超过 10MB 限制")

    # 保存文件
    safe_name = f"{uuid.uuid4().hex}{ext}"
    upload_path = _ensure_upload_dir(task_id)
    dest_path = os.path.join(upload_path, safe_name)

    with open(dest_path, "wb") as f:
        f.write(content)

    now = datetime.now(timezone.utc).isoformat()

    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO files (task_id, file_name, file_path, file_type, file_size) VALUES (?, ?, ?, ?, ?)",
            (task_id, file.filename, dest_path, file_type, len(content)),
        )
        file_id = cursor.lastrowid
        db.commit()

    return FileInfo(
        file_id=file_id,
        file_name=file.filename,
        file_type=file_type,
        file_size=len(content),
        uploaded_at=now,
    )


@router.get("/{task_id}/files", response_model=list[FileInfo])
def list_files(
    task_id: str,
    _=Depends(verify_api_key),
):
    with get_db() as db:
        row = db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        rows = db.execute(
            "SELECT id, file_name, file_type, file_size, uploaded_at FROM files WHERE task_id = ? ORDER BY uploaded_at ASC",
            (task_id,),
        ).fetchall()

    return [
        FileInfo(
            file_id=r["id"],
            file_name=r["file_name"],
            file_type=r["file_type"],
            file_size=r["file_size"],
            uploaded_at=r["uploaded_at"],
        )
        for r in rows
    ]
