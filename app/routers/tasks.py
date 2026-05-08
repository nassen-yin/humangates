import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db
from app.models import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from app.auth import verify_api_key, verify_admin_key

router = APIRouter(tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    body: TaskCreate,
    _=Depends(verify_api_key),
):
    task_id = str(uuid.uuid4()).replace("-", "")
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as db:
        db.execute(
            """INSERT INTO tasks (id, type, status, params, callback_url, created_at, updated_at)
               VALUES (?, ?, 'pending', ?, ?, ?, ?)""",
            (task_id, body.type, json.dumps(body.params, ensure_ascii=False),
             body.callback_url, now, now),
        )
        db.commit()

    return TaskResponse(
        task_id=task_id,
        type=body.type,
        status="pending",
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

        now = datetime.now(timezone.utc).isoformat()
        result_json = json.dumps(body.result, ensure_ascii=False) if body.result else None

        db.execute(
            "UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?",
            (body.status, result_json, now, task_id),
        )
        db.commit()

        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    return _row_to_response(row)


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
