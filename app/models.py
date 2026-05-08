from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class TaskCreate(BaseModel):
    type: str = Field(..., description="任务类型, 例如 company_registration")
    params: Dict[str, Any] = Field(..., description="任务参数")
    callback_url: Optional[str] = Field(None, description="任务完成后的回调地址")


class TaskUpdate(BaseModel):
    status: str = Field(..., description="pending | in_progress | completed | failed")
    result: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    task_id: str
    type: str
    status: str
    params: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
