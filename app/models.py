from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Dict, List


# ── 枚举 ──

VALID_STATUSES = [
    "pending_review",
    "needs_info",
    "materials_ready",
    "in_progress",
    "completed",
    "failed",
]

VALID_TASK_TYPES = ["company_registration"]


# ── 公司注册专用 Schema ──

class Shareholder(BaseModel):
    name: str = Field(..., description="姓名")
    id_number: str = Field(..., description="身份证号")
    phone: str = Field(..., description="手机号")
    capital_contribution: int = Field(..., ge=0, description="出资额（万元）")
    percentage: float = Field(..., ge=0, le=100, description="出资比例（%）")
    role: str = Field(..., description="职务: legal_person / shareholder / supervisor")


class CompanyRegistrationParams(BaseModel):
    company_names: List[str] = Field(..., min_length=1, max_length=5, description="备选公司名，至少1个最多5个")
    business_scope: str = Field(..., min_length=4, description="经营范围描述")
    registered_capital: int = Field(..., ge=1, description="注册资本（万元）")
    shareholders: List[Shareholder] = Field(..., min_length=1, description="股东列表")
    address_type: str = Field(..., description="地址类型: own / lease / virtual")
    address_detail: str = Field(..., min_length=4, description="详细注册地址")
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")

    @field_validator("company_names")
    @classmethod
    def validate_company_names(cls, v):
        for name in v:
            if len(name) < 4:
                raise ValueError(f"公司名太短: {name}")
        return v

    @field_validator("shareholders")
    @classmethod
    def validate_shareholders(cls, v):
        total_pct = sum(s.percentage for s in v)
        if abs(total_pct - 100) > 0.01:
            raise ValueError(f"股东出资比例之和不等于 100%，当前 {total_pct}%")
        # 必须有一个 legal_person
        if not any(s.role == "legal_person" for s in v):
            raise ValueError("必须指定一个法人 (legal_person)")
        # 必须有一个 supervisor (监事)，且法人不能兼任监事
        if not any(s.role == "supervisor" for s in v):
            raise ValueError("必须指定一个监事 (supervisor)")
        for s in v:
            if s.role == "legal_person" and any(t.role == "supervisor" and t.id_number == s.id_number for t in v):
                raise ValueError("法人不能兼任监事")
        return v


# ── 通用模型 ──

class TaskCreate(BaseModel):
    type: str = Field(..., description="任务类型")
    params: Dict[str, Any] = Field(..., description="任务参数")
    callback_url: Optional[str] = Field(None, description="回调地址")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in VALID_TASK_TYPES:
            raise ValueError(f"不支持的任务类型: {v}，支持: {', '.join(VALID_TASK_TYPES)}")
        return v

    @field_validator("params")
    @classmethod
    def validate_params(cls, v, info):
        # 根据 type 校验 params
        task_type = info.data.get("type")
        if task_type == "company_registration":
            CompanyRegistrationParams(**v)
        return v


class TaskUpdate(BaseModel):
    status: str = Field(..., description="新状态")
    result: Optional[Dict[str, Any]] = None
    note: Optional[str] = Field(None, description="状态变更备注")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in VALID_STATUSES:
            raise ValueError(f"无效状态: {v}，支持: {', '.join(VALID_STATUSES)}")
        return v


class TaskNoteCreate(BaseModel):
    note: str = Field(..., min_length=1, description="备注内容")


# ── 文件 ──

class FileInfo(BaseModel):
    file_id: int
    file_name: str
    file_type: str
    file_size: int
    uploaded_at: str


# ── 日志 ──

class TaskLogEntry(BaseModel):
    action: str
    note: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    created_at: str


# ── 响应 ──

class TaskResponse(BaseModel):
    task_id: str
    type: str
    status: str
    params: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None
    created_at: str
    updated_at: str


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# ── 状态机辅助 ──

def get_valid_transitions(status: str) -> List[str]:
    """返回当前状态允许的下一个状态"""
    transitions = {
        "pending_review": ["needs_info", "materials_ready", "failed"],
        "needs_info": ["pending_review", "failed"],
        "materials_ready": ["in_progress", "failed"],
        "in_progress": ["completed", "failed"],
        "completed": [],
        "failed": [],
    }
    return transitions.get(status, [])
