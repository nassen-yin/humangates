from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Dict, List


# ── v0.3 状态机（8 状态）──

VALID_STATUSES = [
    "draft",                    # 初始状态，信息不完整
    "materials_collecting",     # 料收集阶段
    "name_verification",        # 名称核准中
    "submitting",               # 已提交至工商局
    "in_progress",              # 工商局审核中
    "needs_info",               # 需要补充材料（可从任何状态进入）
    "approved",                 # 审核通过
    "completed",                # 已完成（执照已领取）
    "failed",                   # 任务失败
]

# ── 服务能力定义（v0.3 架构）──

CAPABILITIES_COMPANY_REGISTRATION = {
    "status_machine": {
        "initial": "draft",
        "states": VALID_STATUSES,
        "transitions": {
            "draft": ["materials_collecting"],
            "materials_collecting": ["name_verification", "needs_info"],
            "name_verification": ["submitting", "needs_info"],
            "submitting": ["in_progress", "needs_info"],
            "in_progress": ["needs_info", "approved"],
            "needs_info": ["materials_collecting", "submitting"],
            "approved": ["completed"],
            "completed": [],
            "failed": [],
        },
    },
    "agent_auto": {
        "description": "以下判定对方 agent 可独立完成，无需人工介入",
        "items": [
            {"id": "format_validation", "name": "格式校验", "detail": "身份证号、手机号、注册资本、日期等字段格式，由 schema validation.rules 驱动"},
            {"id": "cross_field_validation", "name": "交叉校验", "detail": "出资额求和=注册资本、法人须为股东、监事不得兼任等跨字段逻辑"},
            {"id": "conditional_required", "name": "条件必填判断", "detail": "根据已有字段值判断哪些字段需要补充（如自有房产才需房产证）"},
            {"id": "file_basic_check", "name": "文件基础检查", "detail": "文件类型、大小、OCR可读性检查"},
            {"id": "document_generation", "name": "文书自动生成", "detail": "调用 POST /v1/tasks/{id}/documents，从字段填充模板生成全套文书"},
            {"id": "data_consistency", "name": "文书一致性校验", "detail": "检查生成的所有文件中公司名、股东名、金额是否一致"},
            {"id": "status_transition", "name": "状态流转", "detail": "根据状态机自动推进或退回"},
            {"id": "name_precheck", "name": "名称预检", "detail": "检查名称格式、禁限词、长度等本地规则，通过后才发往工商局"},
            {"id": "name_rejection_auto", "name": "名称驳回自动处理", "detail": "工商局驳回名称时，先查知识库匹配常见驳回原因，匹配成功则自动生成替代方案"},
            {"id": "scope_translation_auto", "name": "经营范围自动转化", "detail": "将客户口头表述的业务描述自动映射为工商标准表述"},
        ],
    },
    "human_required": {
        "description": "以下事项需要真人介入",
        "items": [
            {"id": "government_submission", "name": "工商局递交", "detail": "需要工商系统账号/CA证书/电子营业执照签名"},
            {"id": "rejection_handling", "name": "驳回原因解读", "detail": "工商局驳回理由含自由裁量，需要人工判断补件策略"},
            {"id": "phone_verification", "name": "电话核实", "detail": "工商局/税务来电需真人接听应答"},
            {"id": "signature", "name": "股东签字/企业盖章", "detail": "法律文件需亲笔签字或公章，AI 不可代签"},
            {"id": "exception_handling", "name": "异常流程处理", "detail": "税务登记卡住、地址抽查等非标准流程"},
            {"id": "physical_errand", "name": "线下跑腿", "detail": "某些城市必须线下递交材料/领取证照"},
            {"id": "expediting", "name": "进度催办", "detail": "超时未办结时需真人电话/现场催办"},
        ],
    },
    "escalation": {
        "description": "触发转人的条件",
        "trigger_conditions": [
            {"condition": "工商局返回非结构化驳回", "action": "标记 needs_info + 添加人工处理标签"},
            {"condition": "名称知识库无匹配", "action": "生成3个替代名称建议 + 转人工确认"},
            {"condition": "前置许可需要确认", "action": "标记待人工审核经营范围 + 暂停流程"},
            {"condition": "线下递交要求", "action": "输出准备清单 + 通知人工处理"},
            {"condition": "超时未推进", "action": "标记催办 + 通知人工跟进"},
        ],
    },
    "name_rejection_knowledge_base": {
        "description": "名称驳回知识库，匹配成功则自动生成替代方案",
        "rules": [
            {"pattern": "重名|已存在|已被注册", "country": "全国通用", "suggestion": "更换字号中的关键词，或加行业限定词缩小范围", "priority": 1},
            {"pattern": "近似|相似|容易混淆", "country": "全国通用", "suggestion": "在字号首字前加地域修饰词，或改为三个字字号", "priority": 1},
            {"pattern": "驰名商标|知名品牌", "country": "全国通用", "suggestion": "完全避免使用与驰名商标相同的字词，建议替换核心字", "priority": 1},
            {"pattern": "敏感|禁限|国家|中央|中华|中国|国际", "country": "全国通用", "suggestion": "去除禁限词，如需使用须走特批流程并转人工", "priority": 1},
            {"pattern": "行业表述不规范|行业类别不明确", "country": "全国通用", "suggestion": "参照《国民经济行业分类》调整行业表述", "priority": 2},
            {"pattern": "字号与行业不匹配", "country": "全国通用", "suggestion": "字号需体现行业特征，或修改为中性字号+明确行业限定词", "priority": 2},
        ],
        "auto_action": {
            "matched": "生成3个替代名称 -> 标记待人工快速确认 -> 推送给客户选择",
            "unmatched": "转人工处理（名称知识库无匹配规则）",
        },
    },
    "scope_translation_mapping": {
        "description": "行业关键词->工商标准表述映射表",
        "rules": [
            {"keyword": "做软件|开发软件|编程", "standard": "软件开发；计算机系统服务；技术开发、技术咨询、技术转让、技术推广"},
            {"keyword": "卖东西|电商|网店|网上卖", "standard": "互联网销售（除销售需要许可的商品）；日用百货销售"},
            {"keyword": "做网站|建站|网页设计", "standard": "网络技术服务；网站设计；信息技术咨询服务"},
            {"keyword": "搞培训|上课|教育咨询", "standard": "教育咨询服务（不含涉许可审批的教育培训活动）"},
            {"keyword": "做设计|画图|平面设计", "standard": "专业设计服务；平面设计；图文设计制作"},
            {"keyword": "写代码|做APP|开发小程序", "standard": "软件开发；信息系统集成服务；信息技术咨询服务"},
            {"keyword": "做抖音|新媒体|短视频|直播", "standard": "组织文化艺术交流活动；文化娱乐经纪人服务；互联网信息服务（需许可）"},
            {"keyword": "搞外贸|进出口|做出口", "standard": "货物进出口；技术进出口；进出口代理"},
            {"keyword": "做咨询|顾问|管理咨询", "standard": "企业管理咨询；信息咨询服务（不含许可类信息咨询服务）"},
            {"keyword": "做餐饮|开饭店|开餐厅", "standard": "餐饮服务（需许可）；餐饮管理；食品销售（需许可）"},
            {"keyword": "做建筑|装修|施工", "standard": "建设工程施工（需许可）；建筑装饰材料销售；工程管理服务"},
            {"keyword": "做物流|货运|运输", "standard": "道路货物运输（需许可）；国内货物运输代理；装卸搬运"},
            {"keyword": "做广告|广告设计|推广", "standard": "广告设计、代理；广告发布；广告制作"},
            {"keyword": "做贸易|批发|零售", "standard": "供应链管理服务；国内贸易代理；电子产品销售；五金产品批发；日用百货销售"},
            {"keyword": "做医疗|开诊所|医疗器械", "standard": "医疗服务（需许可）；诊所服务（需许可）；第一类医疗器械销售"},
            {"keyword": "做农业|种地|养殖", "standard": "谷物种植；蔬菜种植；农产品的生产、销售、加工、运输、贮藏"},
            {"keyword": "做酒店|民宿|住宿", "standard": "住宿服务（需许可）；酒店管理；物业管理"},
            {"keyword": "做会展|办活动|策划", "standard": "会议及展览服务；市场营销策划；企业形象策划"},
            {"keyword": "做知识产权|商标|专利", "standard": "知识产权服务（专利代理服务除外）；商标代理；版权代理"},
            {"keyword": "做人力资源|招人|劳务", "standard": "人力资源服务（需许可）；劳务服务（不含劳务派遣）；职业中介活动（需许可）"},
        ],
        "auto_action": {
            "fully_matched": "直接填入经营范围字段，自动归档",
            "partially_matched": "填入已匹配部分 + 高亮未匹配部分 + 标记人工补全",
            "unmatched": "转人工处理",
        },
    },
    "external_services": {
        "description": "Human Gates 不直接对接工商局，通过第三方服务完成递交环节",
        "supported_cities": {
            "tier_1": ["北京", "上海", "广州", "深圳", "杭州"],
            "tier_2": ["成都", "南京", "武汉", "重庆", "天津", "苏州", "宁波"],
            "note_tier_1": "全程线上，e签宝已覆盖，零人工",
            "note_tier_2": "大概率已开通线上，逐个验证后开放",
            "unsupported": "其他城市暂不支持，建议先转人工代办或等待后续开放",
        },
        "registration_provider": {
            "name": "e签宝（esgining）",
            "website": "https://open.esign.cn",
            "integration_type": "API（REST + 回调）",
            "description": "提供实名认证、电子签名、工商注册全流程API",
            "pricing": "SaaS API 标准版 8元/份（按签署份数），实名认证/企业认证免费",
            "api_endpoints": [
                {"method": "POST", "path": "/v3/real-name/auth", "description": "个人实名认证（人脸识别/银联四要素）", "trigger_point": "shareholder_info 收集完成后触发"},
                {"method": "POST", "path": "/v3/organizations/create", "description": "企业实名认证，注册电子印章", "trigger_point": "注册提交前触发"},
                {"method": "POST", "path": "/v3/sign-flow/create", "description": "创建签署流程，指定签署方和文件", "trigger_point": "documents_generation 完成后触发"},
                {"method": "POST", "path": "/v3/sign-flow/{flowId}/execute", "description": "发起签署，通知客户/股东完成电子签名", "trigger_point": "通知客户进行人脸识别+电子签名"},
                {"method": "POST", "path": "/v3/business-registration/submit", "description": "提交至工商局（e签宝已对接各地一网通办）", "trigger_point": "全部签署完成后触发"},
            ],
            "workflow": [
                "1. Human Gates 完成预处理（名称/经营范围/文书生成）",
                "2. -> 调用 e签宝 实名认证 API -> 股东/法人人脸识别",
                "3. -> 调用 e签宝 企业认证 API -> 创建电子印章",
                "4. -> e签宝 发起签署 -> 股东在线电子签名（客户app/小程序）",
                "5. -> 调用 e签宝 工商注册 API -> 提交至工商局",
                "6. -> 接收 e签宝 回调 -> 获取电子营业执照 -> 更新 task 状态",
            ],
            "fallback": {
                "description": "e签宝未覆盖的城市或特殊业务，退回人工代办",
                "trigger_condition": "e签宝返回 unsupported_city 或 registration_rejected",
            },
        },
        "queryable": {
            "description": "对方 agent 可随时查询的流程信息接口",
            "endpoints": [
                {"method": "GET", "path": "/v1/services", "description": "获取所有服务目录及各服务完整 schema"},
                {"method": "GET", "path": "/v1/tasks/{id}", "description": "查询单个任务的当前状态"},
                {"method": "GET", "path": "/v1/tasks/{id}/progress", "description": "流程进度百分比及每步骤状态"},
                {"method": "GET", "path": "/v1/tasks/{id}/documents", "description": "查看已生成的文书列表及状态"},
                {"method": "GET", "path": "/v1/tasks/{id}/audit-log", "description": "完整的操作审计日志"},
            ],
        },
    },
}


# ═══════════════════════════════════════════════
# 服务目录 — API 的第一个问题：你要什么服务？
# ═══════════════════════════════════════════════

class ServiceInfo(BaseModel):
    """返回给 AI 的服务目录条目"""
    type: str
    name: str
    description: str
    status: str  # "live" | "coming_soon" | "planning"
    json_schema: Optional[Dict[str, Any]] = None
    estimated_days: Optional[str] = None
    price_range: Optional[str] = None
    required_documents: Optional[List[str]] = None
    capabilities: Optional[Dict[str, Any]] = None  # v0.3: 完整能力描述

class ServiceListResponse(BaseModel):
    services: List[ServiceInfo]


# ═══════════════════════════════════════════════
# 板块一：公司注册 (company_registration)
# ═══════════════════════════════════════════════

# ── 股东/高管信息 ──

class Shareholder(BaseModel):
    name: str = Field(..., description="股东姓名")
    id_number: str = Field(..., description="身份证号（18位）")
    phone: str = Field(..., description="手机号（11位）")
    capital_contribution: int = Field(..., ge=0, description="出资额（万元）")
    percentage: float = Field(..., ge=0, le=100, description="出资比例（%）")
    role: str = Field(..., description="职务: legal_person / executive_director / manager / supervisor / shareholder")
    residential_address: Optional[str] = Field(None, description="户籍地址或居住地址")
    education: Optional[str] = Field(None, description="学历")
    id_card_valid_from: Optional[str] = Field(None, description="身份证有效期起（YYYY-MM-DD）")
    id_card_valid_until: Optional[str] = Field(None, description="身份证有效期止（YYYY-MM-DD），长期填 'long_term'")
    contribution_method: Optional[str] = Field("货币", description="出资方式：货币 / 实物 / 知识产权 / 土地使用权")
    is_identity_verified: Optional[bool] = Field(False, description="是否已完成工商App实名认证")

class Executive(BaseModel):
    """高管任职信息"""
    role: str = Field(..., description="职务: executive_director / manager / supervisor")
    name: str = Field(..., description="姓名")
    id_number: str = Field(..., description="身份证号")
    tenure: Optional[str] = Field("三年", description="任期年限")

# ── 注册地址 ──

class RegisteredAddress(BaseModel):
    address_type: str = Field(..., description="地址类型: own（自有）/ lease（租赁）/ virtual（园区虚拟地址）")
    address_detail: str = Field(..., min_length=4, description="详细注册地址（精确到门牌号）")
    property_owner_name: Optional[str] = Field(None, description="产权人姓名/名称")
    property_owner_phone: Optional[str] = Field(None, description="产权人联系电话")
    property_cert_number: Optional[str] = Field(None, description="不动产权证号")
    lease_term_years: Optional[int] = Field(None, ge=1, description="租期（年）")
    lease_start_date: Optional[str] = Field(None, description="租赁起始日期（YYYY-MM-DD）")
    is_residential_to_commercial: Optional[bool] = Field(False, description="是否住改商（住宅用作注册地址需居委会盖章）")

# ── 章程关键条款 ──

class ArticlesOfAssociation(BaseModel):
    profit_distribution_ratio: Optional[str] = Field("按出资比例分配", description="利润分配方式")
    voting_rights_ratio: Optional[str] = Field("按出资比例行使", description="表决权行使方式")
    legal_representative: str = Field(..., description="法定代表人产生方式: 执行董事兼任 / 经理担任 / 董事会选举")
    board_establishment: Optional[str] = Field("不设董事会，设执行董事一名", description="董事会设立方式")
    supervisor_establishment: Optional[str] = Field("不设监事会，设监事一名", description="监事会设立方式")
    capital_contribution_deadline: str = Field(..., description="出资期限（YYYY-MM-DD，新法规定最长5年）")

# ── 经营范围（标准化） ──

class BusinessScopeItem(BaseModel):
    code: str = Field(..., description="国民经济行业分类代码（如 I6510）")
    description: str = Field(..., description="经营项目描述")
    is_major: bool = Field(True, description="是否为主营项目")

class BusinessScope(BaseModel):
    industry_category: str = Field(..., description="行业门类（如 I-信息传输、软件和信息技术服务业）")
    items: List[BusinessScopeItem] = Field(..., min_length=1, description="经营项目列表")
    special_items: Optional[List[str]] = Field(None, description="需要前置许可的项目（如食品经营、ICP等）")

# ── 公司注册完整参数 ──

class CompanyRegistrationParams(BaseModel):
    # 公司基本信息
    company_names: List[str] = Field(..., min_length=1, max_length=5, description="备选公司名称，至少1个最多5个")
    registered_capital: int = Field(..., ge=1, description="注册资本（万元）")
    capital_currency: str = Field("人民币", description="注册资本币种")

    # 经营范围
    business_scope: str = Field(..., min_length=4, description="经营范围文字描述")
    business_scope_codes: Optional[List[str]] = Field(None, description="国民经济行业分类代码列表")

    # 股东信息
    shareholders: List[Shareholder] = Field(..., min_length=1, description="股东信息列表（至少1人，最多50人）")

    # 高管任职
    executives: Optional[List[Executive]] = Field(None, description="高管任职安排（不填则默认法人为执行董事兼经理，另设一名监事）")

    # 注册地址
    address: RegisteredAddress

    # 章程条款
    articles: ArticlesOfAssociation

    # 联系人
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")

    # 实名认证状态
    is_all_shareholders_verified: Optional[bool] = Field(False, description="是否所有股东已完成工商App实名认证")
    verification_method: Optional[str] = Field(None, description="实名认证方式: app（工商App）/ face（线下扫脸）/ online（网银认证）")

    # 附加需求
    need_seal: Optional[bool] = Field(True, description="是否需要刻章（公章、财务章、法人章）")
    need_invoice: Optional[bool] = Field(False, description="是否需要申领发票")
    need_bank_account_intro: Optional[bool] = Field(False, description="是否需要推荐银行开户渠道")
    notes: Optional[str] = Field(None, description="补充说明")

    @field_validator("company_names")
    @classmethod
    def validate_company_names(cls, v):
        for name in v:
            if len(name) < 4:
                raise ValueError(f"公司名太短: {name}，至少4个字符")
        return v

    @field_validator("shareholders")
    @classmethod
    def validate_shareholders(cls, v):
        total_pct = sum(s.percentage for s in v)
        if abs(total_pct - 100) > 0.01:
            raise ValueError(f"股东出资比例之和不等于 100%，当前 {total_pct}%")
        if not any(s.role == "legal_person" for s in v):
            raise ValueError("必须指定一个法人 (legal_person)")
        has_supervisor = any(s.role == "supervisor" for s in v)
        if not has_supervisor:
            raise ValueError("必须指定一个监事 (supervisor)")
        for s in v:
            if s.role == "legal_person" and any(t.role == "supervisor" and t.id_number == s.id_number for t in v):
                raise ValueError("法人不能兼任监事")
        return v

    @field_validator("articles")
    @classmethod
    def validate_articles(cls, v):
        if v.capital_contribution_deadline:
            import re
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", v.capital_contribution_deadline):
                raise ValueError(f"出资期限格式错误: {v.capital_contribution_deadline}，应为 YYYY-MM-DD")
        return v


# ═══════════════════════════════════════════════
# 板块二：代理记账 (accounting)
# ═══════════════════════════════════════════════

class AccountingParams(BaseModel):
    company_name: str = Field(..., description="公司全称")
    unified_social_credit_code: str = Field(..., description="统一社会信用代码")
    taxpayer_type: str = Field("小规模纳税人", description="纳税人类型: 小规模纳税人 / 一般纳税人")
    industry: str = Field(..., description="所属行业")
    monthly_invoice_count: Optional[int] = Field(None, description="月均开票量（张）")
    monthly_revenue: Optional[float] = Field(None, description="月均收入（万元）")
    has_employees: Optional[bool] = Field(False, description="是否有雇员")
    employee_count: Optional[int] = Field(0, description="雇员人数")
    need_social_security: Optional[bool] = Field(False, description="是否需要代缴社保")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系人手机号")
    notes: Optional[str] = Field(None, description="补充说明")


# ═══════════════════════════════════════════════
# 服务注册表 — 所有支持的板块在此登记
# ═══════════════════════════════════════════════

def _get_json_schema(model_class) -> Dict[str, Any]:
    """从 Pydantic 模型生成 JSON Schema"""
    return model_class.model_json_schema()


def _inject_validation_rules(schema: Dict[str, Any]) -> Dict[str, Any]:
    """向 JSON Schema 中注入 x-validation 规则（来自 v0.3 设计）"""
    if not schema or "properties" not in schema:
        return schema

    props = schema["properties"]

    # 身份证号 — 格式+校验位+年龄
    for key in list(props.keys()):
        if "id_number" in key or "id_card" in key:
            props[key]["x-validation"] = {
                "rules": [
                    {"rule": "pattern", "pattern": "^\\d{17}[\\dXx]$", "message": "身份证号必须为18位"},
                    {"rule": "checksum", "algorithm": "id_card_checksum", "message": "身份证校验位不正确"},
                ],
                "auto_check": True,
            }

    # 手机号
    if "phone" in props or "contact_phone" in props:
        for key in ["phone", "contact_phone"]:
            if key in props:
                props[key]["x-validation"] = {
                    "rules": [
                        {"rule": "pattern", "pattern": "^1[3-9]\\d{9}$", "message": "手机号格式不正确"}
                    ],
                    "auto_check": True,
                }

    # company_names — 格式校验
    if "company_names" in props:
        props["company_names"]["x-validation"] = {
            "rules": [
                {"rule": "format", "pattern": "^\\p{Han}{2,10}(有限公司|有限责任公司)$", "message": "名称格式：字号+有限公司"},
                {"rule": "blocklist", "keywords": ["国家", "中央", "全国", "中华", "中国", "国际"], "message": "不含禁限词汇"},
            ],
            "auto_check": True,
        }

    # 注册资本
    if "registered_capital" in props:
        props["registered_capital"]["x-validation"] = {
            "rules": [
                {"rule": "integer_or_half", "message": "注册资本通常为整数"},
            ],
            "auto_check": True,
        }

    return schema


SERVICE_REGISTRY = {
    "company_registration": {
        "name": "公司注册",
        "description": "石家庄地区有限责任公司设立。核名 -> 材料准备 -> 工商提交 -> 执照领取，全流程代办。法人无需到场。",
        "status": "live",
        "schema_model": CompanyRegistrationParams,
        "estimated_days": "7-14",
        "price_range": "699-1299",
        "required_documents": [
            "全体股东身份证正反面照片（或扫描件）",
            "法人手机号（用于工商App实名认证）",
            "注册地址证明材料（租赁合同或房产证）",
            "各股东出资比例确认",
            "经营范围描述",
        ],
        "capabilities": CAPABILITIES_COMPANY_REGISTRATION,
        "workflow_steps": [
            {"step_id": "name_verification", "name": "名称核准", "order": 1, "agent_auto": True},
            {"step_id": "shareholder_info", "name": "股东信息", "order": 2, "agent_auto": True},
            {"step_id": "legal_representative", "name": "法定代表人信息", "order": 3, "agent_auto": True},
            {"step_id": "registered_capital", "name": "注册资本", "order": 4, "agent_auto": True},
            {"step_id": "registered_address", "name": "注册地址", "order": 5, "agent_auto": True},
            {"step_id": "business_scope", "name": "经营范围", "order": 6, "agent_auto": True},
            {"step_id": "articles_of_association", "name": "公司章程", "order": 7, "agent_auto": True},
            {"step_id": "document_generation", "name": "文书生成", "order": 8, "agent_auto": True},
            {"step_id": "e_sign_submission", "name": "e签宝递交", "order": 9, "agent_auto": False, "external_service": "e签宝"},
            {"step_id": "governance_review", "name": "工商局审核", "order": 10, "agent_auto": False},
            {"step_id": "license_collection", "name": "执照领取", "order": 11, "agent_auto": False},
        ],
    },
    "accounting": {
        "name": "代理记账",
        "description": "小规模纳税人/一般纳税人月度记账报税，含年度汇算清缴和工商年报。",
        "status": "coming_soon",
        "schema_model": AccountingParams,
        "estimated_days": "持续服务",
        "price_range": "200/月",
        "capabilities": None,
    },
    "tax_registration": {
        "name": "税务登记",
        "description": "新设公司税务登记办理，核定税种，小规模/一般纳税人资格认定。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "3-5",
        "price_range": "待定价",
        "capabilities": None,
    },
    "bank_account": {
        "name": "银行开户",
        "description": "协助预约银行对公账户开户，法人到场陪同，资料预审确保一次通过。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "3-7",
        "price_range": "待定价",
        "capabilities": None,
    },
    "license_application": {
        "name": "资质代办",
        "description": "ICP许可证、食品经营许可证、医疗器械备案等资质申请，材料预审+全程对接审批部门。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "视资质类型",
        "price_range": "按需定价",
        "capabilities": None,
    },
    "company_change": {
        "name": "工商变更",
        "description": "法人变更、股东变更、经营范围变更、注册资本变更、地址变更等全套变更服务。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "5-10",
        "price_range": "500-2000",
        "capabilities": None,
    },
}

VALID_TASK_TYPES = list(SERVICE_REGISTRY.keys())


# ── 通用请求/响应模型 ──

class TaskCreate(BaseModel):
    type: str = Field(..., description="任务类型，调用前先查询 /v1/services 获取可用类型")
    params: Dict[str, Any] = Field(..., description="任务参数，按对应服务类型的 JSON Schema 填写")
    callback_url: Optional[str] = Field(None, description="Webhook 回调地址（任务完成时通知）")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in VALID_TASK_TYPES:
            raise ValueError(
                f"不支持的任务类型: {v}\n"
                f"请先查询 GET /v1/services 查看所有可用类型\n"
                f"当前支持: {', '.join(SERVICE_REGISTRY.keys())}"
            )
        return v

    @field_validator("params")
    @classmethod
    def validate_params(cls, v, info):
        task_type = info.data.get("type")
        if task_type and task_type in SERVICE_REGISTRY:
            model_class = SERVICE_REGISTRY[task_type].get("schema_model")
            if model_class:
                model_class(**v)
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


# ── 新端点响应模型（v0.3）──

class StepProgress(BaseModel):
    step_id: str
    name: str
    status: str  # pending / completed / blocked / in_progress
    pct: int = 0
    blocker: Optional[str] = None

class TaskProgressResponse(BaseModel):
    task_id: str
    current_state: str
    overall_progress_pct: int
    estimated_remaining_days: Optional[int] = None
    step_progress: List[StepProgress]


class DocumentInfo(BaseModel):
    doc_type: str
    doc_name: str
    doc_status: str  # pending / generating / generated / signed / submitted
    file_url: Optional[str] = None
    created_at: Optional[str] = None

class TaskDocumentsResponse(BaseModel):
    task_id: str
    documents: List[DocumentInfo]


class AuditLogEntry(BaseModel):
    action: str
    note: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    created_at: str

class TaskAuditLogResponse(BaseModel):
    task_id: str
    entries: List[AuditLogEntry]


class DocumentGenerateRequest(BaseModel):
    doc_types: Optional[List[str]] = Field(None, description="要生成的文书类型列表。不传则生成全套")

class DocumentGenerateResponse(BaseModel):
    task_id: str
    documents: List[DocumentInfo]


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


# ── 状态机 ──

def get_valid_transitions(status: str) -> List[str]:
    """返回当前状态允许的下一个状态（v0.3 8状态机）"""
    transitions = {
        "draft": ["materials_collecting", "needs_info"],
        "materials_collecting": ["name_verification", "needs_info"],
        "name_verification": ["submitting", "needs_info"],
        "submitting": ["in_progress", "needs_info"],
        "in_progress": ["needs_info", "approved"],
        "needs_info": ["materials_collecting", "submitting"],
        "approved": ["completed"],
        "completed": [],
        "failed": [],
    }
    return transitions.get(status, [])
