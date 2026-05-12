"""服务目录路由 — API 的第一个问题：你要什么服务？"""

from fastapi import APIRouter
from app.models import (
    SERVICE_REGISTRY, ServiceInfo, ServiceListResponse,
    _get_json_schema, _inject_validation_rules,
)

router = APIRouter(tags=["services"])


@router.get("", response_model=ServiceListResponse)
def list_services():
    """返回所有可用服务类型及其完整 JSON Schema 和能力描述。

    AI Agent 调用此端点后，根据返回的 schema 收集用户信息，
    再 POST /v1/tasks 提交任务。

    v0.3 新增：每个服务返回 capabilities 字段，包含：
    - status_machine：8 状态机定义
    - agent_auto：可自动完成的 10 项判定
    - human_required：需要真人介入的事项
    - escalation：触发转人的条件
    - name_rejection_knowledge_base：名称驳回知识库（6 条规则）
    - scope_translation_mapping：经营范围映射表（20 组）
    - external_services：e签宝等第三方服务集成
    - queryable：可查询的进度接口列表
    """
    services = []
    for key, info in SERVICE_REGISTRY.items():
        schema = None
        if info.get("schema_model"):
            try:
                schema = _get_json_schema(info["schema_model"])
                schema = _inject_validation_rules(schema)
            except Exception:
                schema = None

        services.append(ServiceInfo(
            type=key,
            name=info["name"],
            description=info["description"],
            status=info["status"],
            json_schema=schema,
            estimated_days=info.get("estimated_days"),
            price_range=info.get("price_range"),
            required_documents=info.get("required_documents"),
            capabilities=info.get("capabilities"),
        ))

    return ServiceListResponse(services=services)
