"""客户系统 API — 客户管理 + credit充值 + 交易记录"""
import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db
from app.models import (
    CustomerCreate, CustomerUpdate, CustomerInfo, CustomerListResponse,
    CreditRecharge, CreditTransactionInfo, CreditTransactionListResponse,
)
from app.auth import verify_api_key, verify_admin_key

router = APIRouter(tags=["customers"])


def _row_to_customer(row) -> CustomerInfo:
    return CustomerInfo(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        phone=row["phone"],
        company_name=row["company_name"],
        credits_balance=row["credits_balance"],
        total_spent=row["total_spent"],
        total_tasks=row["total_tasks"],
        status=row["status"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post("", response_model=CustomerInfo, status_code=201)
def create_customer(
    body: CustomerCreate,
    _=Depends(verify_admin_key),
):
    """创建客户账户，可选赠送初始credits"""
    customer_id = str(uuid.uuid4()).replace("-", "")
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as db:
        db.execute(
            """INSERT INTO customers (id, name, email, phone, company_name, credits_balance,
               total_spent, total_tasks, status, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)""",
            (customer_id, body.name, body.email, body.phone,
             body.company_name, body.initial_credits, 0, 0,
             body.notes or None, now, now),
        )

        # 如果有初始credits，记录交易
        if body.initial_credits > 0:
            db.execute(
                """INSERT INTO credit_transactions (customer_id, amount, balance_before,
                   balance_after, type, description, created_at)
                   VALUES (?, ?, 0, ?, 'recharge', ?, ?)""",
                (customer_id, body.initial_credits, body.initial_credits,
                 f"新客户赠送 {body.initial_credits} credits", now),
            )

        db.commit()
        row = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()

    return _row_to_customer(row)


@router.get("", response_model=CustomerListResponse)
def list_customers(
    status: str = Query(None, description="按状态过滤: active / disabled"),
    search: str = Query(None, description="按名称/公司名称/邮箱搜索"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _=Depends(verify_admin_key),
):
    """查询客户列表（运营端）"""
    with get_db() as db:
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status)
        if search:
            conditions.append("(name LIKE ? OR company_name LIKE ? OR email LIKE ?)")
            s = f"%{search}%"
            params.extend([s, s, s])

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = db.execute(
            f"SELECT * FROM customers {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        total = db.execute(
            f"SELECT COUNT(*) FROM customers {where}", params
        ).fetchone()[0]

    return CustomerListResponse(
        customers=[_row_to_customer(r) for r in rows],
        total=total,
    )


@router.get("/{customer_id}", response_model=CustomerInfo)
def get_customer(
    customer_id: str,
    _=Depends(verify_admin_key),
):
    """查询单个客户详情"""
    with get_db() as db:
        row = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _row_to_customer(row)


@router.put("/{customer_id}", response_model=CustomerInfo)
def update_customer(
    customer_id: str,
    body: CustomerUpdate,
    _=Depends(verify_admin_key),
):
    """更新客户信息"""
    with get_db() as db:
        row = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")

        updates = {}
        for field in ["name", "email", "phone", "company_name", "status", "notes"]:
            val = getattr(body, field, None)
            if val is not None:
                updates[field] = val

        if not updates:
            return _row_to_customer(row)

        now = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [customer_id]

        db.execute(f"UPDATE customers SET {set_clause} WHERE id = ?", values)
        db.commit()
        row = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()

    return _row_to_customer(row)


@router.post("/{customer_id}/recharge", response_model=CustomerInfo)
def recharge_credits(
    customer_id: str,
    body: CreditRecharge,
    _=Depends(verify_admin_key),
):
    """客户充值 credits（运营端操作）"""
    with get_db() as db:
        row = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")

        now = datetime.now(timezone.utc).isoformat()
        balance_before = row["credits_balance"]
        balance_after = balance_before + body.amount

        db.execute(
            "UPDATE customers SET credits_balance = ?, updated_at = ? WHERE id = ?",
            (balance_after, now, customer_id),
        )
        db.execute(
            """INSERT INTO credit_transactions (customer_id, amount, balance_before,
               balance_after, type, description, created_at)
               VALUES (?, ?, ?, ?, 'recharge', ?, ?)""",
            (customer_id, body.amount, balance_before, balance_after,
             body.description or f"充值 {body.amount} credits", now),
        )
        db.commit()
        row = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()

    return _row_to_customer(row)


@router.get("/{customer_id}/transactions", response_model=CreditTransactionListResponse)
def get_transactions(
    customer_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _=Depends(verify_admin_key),
):
    """查询客户交易记录"""
    with get_db() as db:
        row = db.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")

        rows = db.execute(
            """SELECT * FROM credit_transactions WHERE customer_id = ?
               ORDER BY id DESC LIMIT ? OFFSET ?""",
            (customer_id, limit, offset),
        ).fetchall()
        total = db.execute(
            "SELECT COUNT(*) FROM credit_transactions WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()[0]

    return CreditTransactionListResponse(
        transactions=[
            CreditTransactionInfo(
                id=r["id"],
                customer_id=r["customer_id"],
                task_id=r["task_id"],
                amount=r["amount"],
                balance_before=r["balance_before"],
                balance_after=r["balance_after"],
                type=r["type"],
                description=r["description"],
                created_at=r["created_at"],
            )
            for r in rows
        ],
        total=total,
    )
