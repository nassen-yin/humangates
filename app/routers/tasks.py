import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from app.database import get_db
from app.models import (
    TaskCreate, TaskUpdate, TaskNoteCreate, TaskResponse, TaskListResponse,
    TaskLogEntry, get_valid_transitions,
)
from app.auth import verify_api_key, verify_admin_key

router = APIRouter(tags=["tasks"])


def _log(db, task_id: str, action: str, note: str = None, old_status: str = None, new_status: str = None):
    db.execute(
        "INSERT INTO task_logs (task_id, action, note, old_status, new_status) VALUES (?, ?, ?, ?, ?)",
        (task_id, action, note, old_status, new_status),
    )
    db.commit()


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    body: TaskCreate,
    _=Depends(verify_api_key),
):
    task_id = str(uuid.uuid4()).replace("-", "")
    now = datetime.now(timezone.utc).isoformat()
    status = "pending_review"

    with get_db() as db:
        db.execute(
            """INSERT INTO tasks (id, type, status, params, callback_url, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (task_id, body.type, status, json.dumps(body.params, ensure_ascii=False),
             body.callback_url, now, now),
        )
        _log(db, task_id, "created", note=f"任务创建成功，任务类型: {body.type}", new_status=status)
        db.commit()

    return TaskResponse(
        task_id=task_id,
        type=body.type,
        status=status,
        params=body.params,
        callback_url=body.callback_url,
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: str = Query(None, description="按状态过滤"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _=Depends(verify_api_key),
):
    with get_db() as db:
        if status:
            rows = db.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (status, limit, offset),
            ).fetchall()
            total = db.execute("SELECT COUNT(*) FROM tasks WHERE status = ?", (status,)).fetchone()[0]
        else:
            rows = db.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            total = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    return TaskListResponse(
        tasks=[_row_to_response(r) for r in rows],
        total=total,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    _=Depends(verify_api_key),
):
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    return _row_to_response(row)


@router.put("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: str,
    body: TaskUpdate,
    _=Depends(verify_admin_key),
):
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        old_status = row["status"]
        allowed = get_valid_transitions(old_status)

        if body.status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"状态转换非法: {old_status} → {body.status}，允许: {', '.join(allowed) if allowed else '无（终态）'}",
            )

        now = datetime.now(timezone.utc).isoformat()
        result_json = json.dumps(body.result, ensure_ascii=False) if body.result else None

        db.execute(
            "UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?",
            (body.status, result_json, now, task_id),
        )
        _log(db, task_id, "status_change", note=body.note,
             old_status=old_status, new_status=body.status)
        db.commit()

        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    return _row_to_response(row)


@router.post("/{task_id}/notes", response_model=dict)
def add_note(
    task_id: str,
    body: TaskNoteCreate,
    _=Depends(verify_admin_key),
):
    with get_db() as db:
        row = db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        _log(db, task_id, "note", note=body.note)
        db.commit()

    return {"status": "ok", "note": body.note}


@router.get("/{task_id}/timeline", response_model=list[TaskLogEntry])
def get_timeline(
    task_id: str,
    _=Depends(verify_api_key),
):
    with get_db() as db:
        row = db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        logs = db.execute(
            "SELECT action, note, old_status, new_status, created_at FROM task_logs WHERE task_id = ? ORDER BY id ASC",
            (task_id,),
        ).fetchall()

    return [
        TaskLogEntry(
            action=log["action"],
            note=log["note"],
            old_status=log["old_status"],
            new_status=log["new_status"],
            created_at=log["created_at"],
        )
        for log in logs
    ]


def _row_to_response(row) -> TaskResponse:
    return TaskResponse(
        task_id=row["id"],
        type=row["type"],
        status=row["status"],
        params=json.loads(row["params"]) if isinstance(row["params"], str) else {},
        result=json.loads(row["result"]) if row["result"] and isinstance(row["result"], str) else (row["result"] or None),
        callback_url=row["callback_url"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
