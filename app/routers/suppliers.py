"""服务商入驻 + 审核管理 API（v0.5.0 增强版）"""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db
from app.models import (
    SupplierCreate, SupplierUpdate, SupplierInfoUpdate, SupplierInfo, SupplierListResponse,
    VALID_SUPPLIER_STATUSES, SERVICE_PRICING,
)
from app.auth import verify_api_key, verify_admin_key

router = APIRouter(tags=["suppliers"])


@router.post("/register", status_code=201)
def register_supplier(body: SupplierCreate):
    """公开接口：服务商自助入驻（v0.5.0 增强版，支持区域/专长）"""
    with get_db() as db:
        db.execute(
            """INSERT INTO suppliers (name, phone, wechat, city, service_types, regions, specialties,
               id_number, qualification_desc)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (body.name, body.phone, body.wechat, body.city,
             json.dumps(body.service_types, ensure_ascii=False),
             json.dumps(body.regions, ensure_ascii=False),
             json.dumps(body.specialties, ensure_ascii=False),
             body.id_number, body.qualification_desc),
        )
        db.commit()
        row = db.execute("SELECT id FROM suppliers ORDER BY id DESC LIMIT 1").fetchone()

    return {"success": True, "supplier_id": row["id"], "status": "pending"}


@router.get("", response_model=SupplierListResponse)
def list_suppliers(
    status: str = Query(None, description="按状态过滤: pending/approved/rejected"),
    city: str = Query(None, description="按城市筛选"),
    service_type: str = Query(None, description="按服务品类ID筛选"),
    region: str = Query(None, description="按覆盖区域筛选"),
    specialty: str = Query(None, description="按专长筛选"),
    verified: bool = Query(None, description="仅看已认证"),
    available: bool = Query(None, description="仅看可接单"),
    min_rating: float = Query(None, ge=0, le=5, description="最低评分"),
    search: str = Query(None, description="搜索名称/电话"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _=Depends(verify_admin_key),
):
    """运营端：查询供应商列表（v0.5.0 增强筛选）"""
    with get_db() as db:
        conditions = []
        params = []

        if status:
            conditions.append("s.status = ?")
            params.append(status)
        if city:
            conditions.append("s.city LIKE ?")
            params.append(f"%{city}%")
        if service_type:
            conditions.append("s.service_types LIKE ?")
            params.append(f"%{service_type}%")
        if region:
            conditions.append("s.regions LIKE ?")
            params.append(f"%{region}%")
        if specialty:
            conditions.append("s.specialties LIKE ?")
            params.append(f"%{specialty}%")
        if verified is not None:
            conditions.append("s.verified = ?")
            params.append(1 if verified else 0)
        if available is not None:
            conditions.append("s.available = ?")
            params.append(1 if available else 0)
        if min_rating is not None:
            conditions.append("s.rating >= ?")
            params.append(min_rating)
        if search:
            conditions.append("(s.name LIKE ? OR s.phone LIKE ?)")
            s = f"%{search}%"
            params.extend([s, s])

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = db.execute(
            f"SELECT s.* FROM suppliers s {where} ORDER BY s.rating DESC, s.completed_tasks DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        total = db.execute(
            f"SELECT COUNT(*) FROM suppliers s {where}", params
        ).fetchone()[0]

    return SupplierListResponse(
        suppliers=[_row_to_supplier(r) for r in rows],
        total=total,
    )


@router.get("/search/available", response_model=SupplierListResponse)
def find_suppliers(
    service_type: str = Query(..., description="服务品类ID"),
    city: str = Query("", description="城市（可选）"),
    region: str = Query("", description="覆盖区域（可选）"),
    _=Depends(verify_api_key),
):
    """公开接口：按服务品类查找可用供应商（用于任务自动派单）"""
    with get_db() as db:
        conditions = ["s.status = 'approved'", "s.available = 1"]
        params = []

        conditions.append("s.service_types LIKE ?")
        params.append(f"%{service_type}%")

        if city:
            conditions.append("(s.city LIKE ? OR s.regions LIKE ?)")
            c = f"%{city}%"
            params.extend([c, c])
        if region:
            conditions.append("s.regions LIKE ?")
            params.append(f"%{region}%")

        where = "WHERE " + " AND ".join(conditions)
        rows = db.execute(
            f"SELECT s.* FROM suppliers s {where} ORDER BY s.rating DESC, s.completed_tasks DESC LIMIT 10",
            params,
        ).fetchall()
        total = len(rows)

    return SupplierListResponse(
        suppliers=[_row_to_supplier(r) for r in rows],
        total=total,
    )


@router.get("/{supplier_id}", response_model=SupplierInfo)
def get_supplier(
    supplier_id: int,
    _=Depends(verify_admin_key),
):
    """查询单个供应商详情"""
    with get_db() as db:
        row = db.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _row_to_supplier(row)


@router.put("/{supplier_id}/review", response_model=SupplierInfo)
def review_supplier(
    supplier_id: int,
    body: SupplierUpdate,
    _=Depends(verify_admin_key),
):
    """运营端：审核通过或驳回供应商入驻申请"""
    if body.status not in VALID_SUPPLIER_STATUSES:
        raise HTTPException(status_code=400, detail=f"状态必须为: {', '.join(VALID_SUPPLIER_STATUSES)}")

    with get_db() as db:
        row = db.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Supplier not found")

        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "UPDATE suppliers SET status = ?, notes = ?, updated_at = ? WHERE id = ?",
            (body.status, body.notes, now, supplier_id),
        )
        db.commit()
        row = db.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
    return _row_to_supplier(row)


@router.put("/{supplier_id}/info", response_model=SupplierInfo)
def update_supplier_info(
    supplier_id: int,
    body: SupplierInfoUpdate,
    _=Depends(verify_admin_key),
):
    """运营端：更新供应商详细信息（区域/专长/评分/认证/可用性）"""
    with get_db() as db:
        row = db.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Supplier not found")

        updates = {}
        now = datetime.now(timezone.utc).isoformat()

        if body.regions is not None:
            updates["regions"] = json.dumps(body.regions, ensure_ascii=False)
        if body.specialties is not None:
            updates["specialties"] = json.dumps(body.specialties, ensure_ascii=False)
        if body.rating is not None:
            updates["rating"] = body.rating
        if body.verified is not None:
            updates["verified"] = 1 if body.verified else 0
        if body.available is not None:
            updates["available"] = 1 if body.available else 0
        if body.notes is not None:
            updates["notes"] = body.notes

        if updates:
            updates["updated_at"] = now
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [supplier_id]
            db.execute(f"UPDATE suppliers SET {set_clause} WHERE id = ?", values)
            db.commit()

        row = db.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
    return _row_to_supplier(row)


def _row_to_supplier(row) -> SupplierInfo:
    return SupplierInfo(
        id=row["id"],
        name=row["name"],
        phone=row["phone"],
        wechat=row["wechat"],
        city=row["city"],
        service_types=json.loads(row["service_types"]) if isinstance(row["service_types"], str) else [],
        regions=json.loads(row["regions"]) if isinstance(row.get("regions"), str) else [],
        specialties=json.loads(row["specialties"]) if isinstance(row.get("specialties"), str) else [],
        id_number=row["id_number"],
        qualification_desc=row["qualification_desc"],
        status=row["status"],
        rating=row.get("rating", 0) or 0,
        completed_tasks=row.get("completed_tasks", 0) or 0,
        verified=bool(row.get("verified", 0)),
        available=bool(row.get("available", 1)),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
