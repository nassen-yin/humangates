import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from app.database import get_db
from app.models import (
    TaskCreate, TaskUpdate, TaskNoteCreate, TaskResponse, TaskListResponse,
    TaskLogEntry, get_valid_transitions, DashboardResponse,
    SERVICE_PRICING,
)
from app.auth import verify_api_key, verify_admin_key

router = APIRouter(tags=["tasks"])


def _log(db, task_id: str, action: str, note: str = None, old_status: str = None, new_status: str = None):
    db.execute(
        "INSERT INTO task_logs (task_id, action, note, old_status, new_status) VALUES (?, ?, ?, ?, ?)",
        (task_id, action, note, old_status, new_status),
    )
    db.commit()


def _get_price(service_type: str) -> float:
    """根据服务类型获取 base price"""
    pricing = SERVICE_PRICING.get(service_type, {})
    return pricing.get("base_price", 0)


def _deduct_credits(db, customer_id: str, task_id: str, amount: float, service_type: str):
    """从客户账户扣款"""
    row = db.execute("SELECT credits_balance FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")
    if row["credits_balance"] < amount:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits: balance={row['credits_balance']}, required={amount}. Please recharge.",
        )

    now = datetime.now(timezone.utc).isoformat()
    balance_before = row["credits_balance"]
    balance_after = balance_before - amount

    db.execute(
        "UPDATE customers SET credits_balance = ?, total_spent = total_spent + ?, total_tasks = total_tasks + 1, updated_at = ? WHERE id = ?",
        (balance_after, amount, now, customer_id),
    )
    db.execute(
        """INSERT INTO credit_transactions (customer_id, task_id, amount, balance_before, balance_after, type, description, created_at)
           VALUES (?, ?, ?, ?, ?, 'task_payment', ?, ?)""",
        (customer_id, task_id, -amount, balance_before, balance_after,
         f"任务扣款: {service_type} ({amount} credits)", now),
    )


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    body: TaskCreate,
    _=Depends(verify_api_key),
):
    task_id = str(uuid.uuid4()).replace("-", "")
    now = datetime.now(timezone.utc).isoformat()
    status = "draft"
    price = _get_price(body.type)

    with get_db() as db:
        # 如果传了 customer_id，先扣款再创建任务（原子操作）
        if body.customer_id and price > 0:
            _deduct_credits(db, body.customer_id, task_id, price, body.type)

        db.execute(
            """INSERT INTO tasks (id, type, status, params, callback_url, customer_id, price, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, body.type, status, json.dumps(body.params, ensure_ascii=False),
             body.callback_url, body.customer_id, price, now, now),
        )
        _log(db, task_id, "created",
             note=f"任务创建成功，类型: {body.type}{f'，扣费 {price} credits' if body.customer_id and price > 0 else ''}",
             new_status=status)
        db.commit()

    return TaskResponse(
        task_id=task_id,
        type=body.type,
        status=status,
        params=body.params,
        callback_url=body.callback_url,
        customer_id=body.customer_id,
        price=price,
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: str = Query(None, description="按状态过滤"),
    customer_id: str = Query(None, description="按客户ID过滤"),
    type: str = Query(None, description="按服务类型过滤"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _=Depends(verify_api_key),
):
    with get_db() as db:
        conditions = []
        params = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if customer_id:
            conditions.append("customer_id = ?")
            params.append(customer_id)
        if type:
            conditions.append("type = ?")
            params.append(type)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = db.execute(
            f"SELECT * FROM tasks {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        total = db.execute(
            f"SELECT COUNT(*) FROM tasks {where}", params
        ).fetchone()[0]

    return TaskListResponse(
        tasks=[_row_to_response(r) for r in rows],
        total=total,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    _=Depends(verify_admin_key),
):
    """运营面板：任务、供应商、客户统计数据"""
    with get_db() as db:
        # Tasks
        task_rows = db.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ).fetchall()
        task_counts = {r["status"]: r["cnt"] for r in task_rows}
        total_tasks = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

        # Suppliers
        supplier_rows = db.execute(
            "SELECT status, COUNT(*) as cnt FROM suppliers GROUP BY status"
        ).fetchall()
        supplier_counts = {r["status"]: r["cnt"] for r in supplier_rows}
        total_suppliers = db.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]

        # Customers (v0.5.0)
        customer_rows = db.execute(
            "SELECT status, COUNT(*) as cnt FROM customers GROUP BY status"
        ).fetchall()
        customer_counts = {r["status"]: r["cnt"] for r in customer_rows}
        total_customers = db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        total_credits = db.execute("SELECT COALESCE(SUM(credits_balance), 0) FROM customers").fetchone()[0]

    return DashboardResponse(
        task_counts=task_counts,
        total_tasks=total_tasks,
        supplier_counts=supplier_counts,
        total_suppliers=total_suppliers,
        customer_counts=customer_counts,
        total_customers=total_customers,
        total_credits_in_system=total_credits,
    )


@router.get("/pricing", response_model=dict)
def get_pricing(
    _=Depends(verify_api_key),
):
    """获取所有服务的定价（credits计价）"""
    return {
        "currency": "credits",
        "description": "1 credit ≈ 1 RMB。充值请联系运营。",
        "services": SERVICE_PRICING,
    }


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
        customer_id=row.get("customer_id"),
        price=row.get("price", 0),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
