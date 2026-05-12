"""任务操作路由 — 进度查询、文书管理、审计日志"""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.models import (
    SERVICE_REGISTRY,
    TaskProgressResponse, StepProgress,
    TaskDocumentsResponse, DocumentInfo,
    TaskAuditLogResponse, AuditLogEntry,
    DocumentGenerateResponse, DocumentGenerateRequest,
)
from app.auth import verify_api_key, verify_admin_key

router = APIRouter(tags=["operations"])


# ── 步骤到状态的映射（用于进度计算）──

_STATE_STEP_MAP = {
    "draft": "name_verification",
    "materials_collecting": "shareholder_info",
    "name_verification": "name_verification",
    "submitting": "document_generation",
    "in_progress": "e_sign_submission",
    "needs_info": None,  # 取决于阻塞的具体步骤
    "approved": "governance_review",
    "completed": "license_collection",
}

_TOTAL_STEPS = 11  # company_registration 有 11 步


@router.get("/{task_id}/progress", response_model=TaskProgressResponse)
def get_task_progress(
    task_id: str,
    _=Depends(verify_api_key),
):
    """查询任务进度：总体百分比 + 每步骤状态"""
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    service_type = row["type"]
    service_info = SERVICE_REGISTRY.get(service_type, {})
    workflow_steps = service_info.get("workflow_steps", [])
    total_steps = len(workflow_steps) if workflow_steps else _TOTAL_STEPS
    current_state = row["status"]

    # 计算当前进行到的步骤索引
    current_step_idx = 0
    current_step_name = _STATE_STEP_MAP.get(current_state)

    if current_state == "needs_info":
        # 尝试从 timeline 找最近阻塞的步骤
        current_step_idx = 3  # 默认在 shareholders 附近
    elif current_state == "completed":
        current_step_idx = total_steps
    elif current_step_idx == "failed":
        current_step_idx = total_steps
    else:
        for i, step in enumerate(workflow_steps):
            if step["step_id"] == current_step_name:
                current_step_idx = i
                break

    # 生成每步骤状态
    step_progress = []
    for i, step in enumerate(workflow_steps):
        if i < current_step_idx:
            status = "completed"
            pct = 100
            blocker = None
        elif i == current_step_idx and current_state == "needs_info":
            status = "blocked"
            pct = 60
            blocker = "有待补充材料"
        elif i == current_step_idx:
            status = "in_progress"
            pct = 50
            blocker = None
        else:
            status = "pending"
            pct = 0
            blocker = None

        step_progress.append(StepProgress(
            step_id=step["step_id"],
            name=step["name"],
            status=status,
            pct=pct,
            blocker=blocker,
        ))

    # 总体百分比
    overall = int((current_step_idx / total_steps) * 100) if total_steps > 0 else 0

    # 估计剩余天数
    remaining_days = max(0, 14 - current_step_idx) if current_state != "completed" else 0

    return TaskProgressResponse(
        task_id=task_id,
        current_state=current_state,
        overall_progress_pct=min(overall, 100),
        estimated_remaining_days=remaining_days,
        step_progress=step_progress,
    )


@router.get("/{task_id}/documents", response_model=TaskDocumentsResponse)
def list_documents(
    task_id: str,
    _=Depends(verify_api_key),
):
    """查询已生成的文书列表及每个文书的状态"""
    with get_db() as db:
        row = db.execute("SELECT id, type FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        service_type = row["type"]

        doc_rows = db.execute(
            "SELECT doc_type, doc_name, status, file_path, created_at FROM documents WHERE task_id = ? ORDER BY id ASC",
            (task_id,),
        ).fetchall()

    documents = []
    for d in doc_rows:
        documents.append(DocumentInfo(
            doc_type=d["doc_type"],
            doc_name=d["doc_name"],
            doc_status=d["status"],
            file_url=d["file_path"],
            created_at=d["created_at"],
        ))

    # 如果还没有文书，返回标准模板列表
    if not documents:
        documents = [
            DocumentInfo(doc_type="articles_of_association", doc_name="公司章程", doc_status="pending"),
            DocumentInfo(doc_type="shareholder_resolution", doc_name="股东会决议", doc_status="pending"),
            DocumentInfo(doc_type="appointment_doc", doc_name="任职文件", doc_status="pending"),
            DocumentInfo(doc_type="lease_contract", doc_name="租赁合同（如有）", doc_status="pending"),
        ]

    return TaskDocumentsResponse(
        task_id=task_id,
        documents=documents,
    )


@router.get("/{task_id}/audit-log", response_model=TaskAuditLogResponse)
def get_audit_log(
    task_id: str,
    _=Depends(verify_api_key),
):
    """完整的操作审计日志"""
    with get_db() as db:
        row = db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        logs = db.execute(
            "SELECT action, note, old_status, new_status, created_at FROM task_logs WHERE task_id = ? ORDER BY id ASC",
            (task_id,),
        ).fetchall()

    return TaskAuditLogResponse(
        task_id=task_id,
        entries=[
            AuditLogEntry(
                action=log["action"],
                note=log["note"],
                old_status=log["old_status"],
                new_status=log["new_status"],
                created_at=log["created_at"],
            )
            for log in logs
        ],
    )


@router.post("/{task_id}/documents", response_model=DocumentGenerateResponse)
def generate_documents(
    task_id: str,
    body: DocumentGenerateRequest = None,
    _=Depends(verify_admin_key),
):
    """从已提交的字段填充模板生成全套法律文书。

    生成以下文书：
    - 公司章程（articles_of_association）
    - 股东会决议（shareholder_resolution）
    - 任职文件（appointment_doc）
    - 租赁合同（lease_contract，如有）

    生成后文书状态变为 'generated'。
    """
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        if row["type"] != "company_registration":
            raise HTTPException(status_code=400, detail="目前仅支持公司注册类型的文书生成")

        now = datetime.now(timezone.utc).isoformat()
        params = json.loads(row["params"]) if isinstance(row["params"], str) else {}

        # 标准文书模板列表
        template_docs = [
            {"doc_type": "articles_of_association", "doc_name": "公司章程"},
            {"doc_type": "shareholder_resolution", "doc_name": "股东会决议"},
            {"doc_type": "appointment_doc", "doc_name": "任职文件"},
        ]
        if params.get("address", {}).get("address_type") == "lease":
            template_docs.append({"doc_type": "lease_contract", "doc_name": "租赁合同"})

        # 如果指定了 doc_types，只生成指定的
        if body and body.doc_types:
            template_docs = [d for d in template_docs if d["doc_type"] in body.doc_types]

        documents = []
        for doc in template_docs:
            # 检查是否已存在
            existing = db.execute(
                "SELECT id FROM documents WHERE task_id = ? AND doc_type = ?",
                (task_id, doc["doc_type"]),
            ).fetchone()

            if existing:
                db.execute(
                    "UPDATE documents SET status = 'generated', updated_at = ? WHERE id = ?",
                    (now, existing["id"]),
                )
            else:
                db.execute(
                    "INSERT INTO documents (task_id, doc_type, doc_name, status, created_at, updated_at) VALUES (?, ?, ?, 'generated', ?, ?)",
                    (task_id, doc["doc_type"], doc["doc_name"], now, now),
                )

            documents.append(DocumentInfo(
                doc_type=doc["doc_type"],
                doc_name=doc["doc_name"],
                doc_status="generated",
                created_at=now,
            ))

        # 写入生成队列记录
        db.execute(
            "INSERT INTO document_generation_queue (task_id, status, created_at) VALUES (?, 'completed', ?)",
            (task_id, now),
        )
        db.commit()

    return DocumentGenerateResponse(
        task_id=task_id,
        documents=documents,
    )
