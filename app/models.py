from pydantic import BaseModel, Field, field_validator, model_validator
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
# 板块三：高企认定/专精特新 (high_tech_application)
# ═══════════════════════════════════════════════

HIGH_TECH_STATUSES = [
    "draft",                    # 初始状态，信息不完整
    "materials_collecting",     # 材料收集阶段
    "submitting",               # 已提交至主管部门
    "in_review",                # 评审中
    "needs_info",               # 需要补充材料（可从任何状态进入）
    "approved",                 # 审核通过
    "failed",                   # 任务失败
]

CAPABILITIES_HIGH_TECH = {
    "status_machine": {
        "initial": "draft",
        "states": HIGH_TECH_STATUSES,
        "transitions": {
            "draft": ["materials_collecting"],
            "materials_collecting": ["submitting", "needs_info"],
            "submitting": ["in_review", "needs_info"],
            "in_review": ["needs_info", "approved", "failed"],
            "needs_info": ["materials_collecting", "submitting"],
            "approved": [],
            "failed": [],
        },
    },
    "agent_auto": {
        "description": "以下判定对方 agent 可独立完成，无需人工介入",
        "items": [
            {"id": "ip_audit", "name": "知识产权审计", "detail": "自动审核专利/软著数量、类型、有效期，按评分标准折算分值"},
            {"id": "financial_check", "name": "财务数据审核", "detail": "核查近三年营收、净资产、研发费用占比是否符合认定门槛"},
            {"id": "rd_staff_ratio", "name": "研发人员比例核算", "detail": "统计研发人员占员工总数比例，自动比对认定标准"},
            {"id": "score_pre_evaluation", "name": "评分预评估", "detail": "根据四大维度（知识产权、成果转化、研发管理、成长性）自动打分并预测通过概率"},
            {"id": "document_completeness", "name": "材料完整性检查", "detail": "逐项检查认定所需全套材料的提交状态，标记缺失项"},
            {"id": "format_validation", "name": "格式校验", "detail": "校验上传文件的格式、大小、命名规范及OCR可读性"},
        ],
    },
    "human_required": {
        "description": "以下事项需要真人介入",
        "items": [
            {"id": "expert_interview_prep", "name": "专家答辩辅导", "detail": "高企认定含专家评审环节，需要组织客户进行答辩模拟和材料完善"},
            {"id": "government_submission", "name": "系统提交至主管部门", "detail": "需要登录各地科技/经信部门系统进行最终提交（含CA/电子印章）"},
            {"id": "on_site_inspection", "name": "现场考察陪同", "detail": "部分认定需要实地考察企业研发场所，需专人陪同接待"},
            {"id": "audit_firm_coordination", "name": "审计事务所协调", "detail": "需要具备资质的审计事务所出具专项审计报告（研发费用/高新技术产品收入）"},
            {"id": "rejection_appeal", "name": "认定驳回申诉", "detail": "认定结果驳回后，需要人工分析原因并组织复核/申诉材料"},
        ],
    },
    "escalation": {
        "description": "触发转人的条件",
        "trigger_conditions": [
            {"condition": "财务指标不达标", "action": "标记暂不符合认定条件 + 输出改善建议 + 通知客户 + 转人工跟进咨询"},
            {"condition": "知识产权数量不足", "action": "标记知识产权缺口 + 建议加急申请专利或软著 + 转人工协调办理"},
            {"condition": "研发人员占比低于10%", "action": "标记人员结构不达标 + 建议调整组织架构或补充社保记录 + 转人工沟通"},
            {"condition": "认定截止日期临近", "action": "标记紧急状态 + 输出加急处理清单 + 通知人工优先排队处理"},
        ],
    },
    "knowledge_base": {
        "description": "高企认定评分标准和资质类型知识库",
        "scoring_criteria": [
            {
                "dimension": "知识产权（≤30分）",
                "score": 30,
                "key_factors": ["发明专利每项7-8分", "实用新型每项2分", "软著每项1-2分", "集成电路布图每项5分", "数量6项以上为A档"],
            },
            {
                "dimension": "科技成果转化能力（≤30分）",
                "score": 30,
                "key_factors": ["年均5项以上为A档", "需提供转化证明（合同/发票/检测报告）", "成果形式包括专利/软著/技术诀窍等"],
            },
            {
                "dimension": "研究开发组织管理水平（≤20分）",
                "score": 20,
                "key_factors": ["研发立项管理制度", "研发投入核算体系", "产学研合作协议", "研发人员绩效考核制度", "科技成果转化激励制度"],
            },
            {
                "dimension": "企业成长性（≤20分）",
                "score": 20,
                "key_factors": ["净资产增长率（≤10分）", "销售收入增长率（≤10分）", "近三年数据均正增长为A档"],
            },
        ],
        "qualification_types": [
            {
                "type": "high_tech",
                "name": "高新技术企业认定",
                "description": "科技部认定的国家级高企，享受15%企业所得税优惠税率",
                "basic_requirements": ["注册成立一年以上", "核心知识产权自主所有", "研发人员占比≥10%", "近三年研发费用占销售收入比例达标（<5000万≥5%，5000万-2亿≥4%，>2亿≥3%）", "高新收入占总收入≥60%"],
            },
            {
                "type": "specialized_sme",
                "name": "专精特新中小企业",
                "description": "省级经信部门认定的专业化、精细化、特色化、新颖化中小企业",
                "basic_requirements": ["注册成立两年以上", "上年营收≥1000万元", "研发投入占比≥3%", "拥有至少2项知识产权", "专业化/精细化/特色化/新颖化四维度评分达标"],
            },
            {
                "type": "little_giant",
                "name": "专精特新小巨人企业",
                "description": "国家级专精特新小巨人，最高级别认定，享受中央财政重点支持",
                "basic_requirements": ["已认定为省级专精特新中小企业", "上年营收≥1亿元（非重点领域可放宽至5000万）", "研发投入占比≥3%且研发人员占比≥15%", "拥有至少5项核心发明专利", "主导产品在细分市场占有率排名前列"],
            },
        ],
    },
}


class IpItem(BaseModel):
    type: str = Field(..., description="知识产权类型: invention（发明专利）/ utility（实用新型）/ design（外观设计）/ copyright（软著）")
    name: str = Field(..., min_length=1, description="知识产权名称")
    reg_number: str = Field(..., min_length=1, description="授权号/登记号")
    status: str = Field(..., description="状态: granted（已授权）/ pending（审查中）/ expired（已过期）")
    grant_date: str = Field(..., description="授权日期（YYYY-MM-DD）")

class FinancialYearData(BaseModel):
    year: int = Field(..., description="年度（如2023）")
    revenue: float = Field(..., ge=0, description="营业收入（万元）")
    rd_expenses: float = Field(..., ge=0, description="研发费用（万元）")
    total_assets: float = Field(..., ge=0, description="总资产（万元）")
    net_profit: float = Field(..., description="净利润（万元，可负值）")

class StaffInfo(BaseModel):
    total_employees: int = Field(..., ge=1, description="员工总数")
    rd_employees: int = Field(..., ge=0, description="研发人员数")
    education_stats: Optional[Dict[str, int]] = Field(None, description="学历分布统计（如 {\"硕士\": 5, \"本科\": 20, \"大专及以下\": 10}）")

class HighTechProduct(BaseModel):
    name: str = Field(..., min_length=1, description="高新技术产品/服务名称")
    revenue_ratio: float = Field(..., ge=0, le=100, description="产品收入占高新总收入比例（%）")
    related_ip: Optional[List[str]] = Field(None, description="关联的知识产权名称列表")

class HighTechApplicationParams(BaseModel):
    # 企业基本信息
    company_name: str = Field(..., min_length=1, description="企业全称")
    unified_social_credit_code: str = Field(..., min_length=18, max_length=18, description="统一社会信用代码（18位）")
    registration_date: str = Field(..., description="注册成立日期（YYYY-MM-DD）")
    registered_capital: float = Field(..., ge=1, description="注册资本（万元）")

    # 行业与核心技术
    industry: str = Field(..., min_length=1, description="所属行业（按国民经济行业分类）")
    core_technology_description: str = Field(..., min_length=10, description="核心技术描述（简要说明主要技术方向及创新点）")

    # 知识产权组合
    ip_portfolio: List[IpItem] = Field(..., min_length=1, description="知识产权组合列表")

    # 近三年财务数据
    financials_3_years: List[FinancialYearData] = Field(..., min_length=3, max_length=3, description="近三年财务数据（需3年，精确到万元）")

    # 人员信息
    staff_info: StaffInfo = Field(..., description="人员结构信息")

    # 高新产品/服务
    high_tech_products: List[HighTechProduct] = Field(..., min_length=1, description="高新技术产品/服务列表")

    # 申请类型
    application_type: str = Field(..., description="认定类型: high_tech（高新技术企业）/ specialized_sme（专精特新中小企业）/ little_giant（专精特新小巨人）")

    # 联系人
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")

    # 备注
    notes: Optional[str] = Field(None, description="补充说明")

    @field_validator("unified_social_credit_code")
    @classmethod
    def validate_credit_code(cls, v):
        if len(v) != 18:
            raise ValueError(f"统一社会信用代码必须为18位，当前{v}长度{len(v)}")
        return v

    @field_validator("ip_portfolio")
    @classmethod
    def validate_ip_portfolio(cls, v):
        if len(v) < 1:
            raise ValueError("至少需要1项知识产权")
        valid_types = {"invention", "utility", "design", "copyright"}
        for ip in v:
            if ip.type not in valid_types:
                raise ValueError(f"无效的知识产权类型: {ip.type}，支持: {', '.join(valid_types)}")
        return v

    @field_validator("staff_info")
    @classmethod
    def validate_staff_ratio(cls, v):
        if v.rd_employees > v.total_employees:
            raise ValueError(f"研发人员数（{v.rd_employees}）不能超过员工总数（{v.total_employees}）")
        rd_ratio = v.rd_employees / v.total_employees * 100
        if rd_ratio < 10:
            raise ValueError(f"研发人员占比必须≥10%，当前为 {rd_ratio:.1f}%")
        return v

    @field_validator("financials_3_years")
    @classmethod
    def validate_financials(cls, v):
        if len(v) != 3:
            raise ValueError(f"需要恰好3年的财务数据，当前提供{len(v)}年")
        years = [fy.year for fy in v]
        if len(set(years)) != 3:
            raise ValueError("财务数据年份不能重复")
        total_rd = sum(fy.rd_expenses for fy in v)
        total_revenue = sum(fy.revenue for fy in v)
        if total_revenue > 0:
            rd_pct = total_rd / total_revenue * 100
            # 简化校验：综合研发占比不低于3%（各类型标准不同，此处仅做基本检查）
            if rd_pct < 1:
                raise ValueError(f"近三年研发费用占营业收入比例异常偏低（{rd_pct:.2f}%），请核实数据")
        return v

    @field_validator("application_type")
    @classmethod
    def validate_application_type(cls, v):
        valid_types = {"high_tech", "specialized_sme", "little_giant"}
        if v not in valid_types:
            raise ValueError(f"无效的认定类型: {v}，支持: {', '.join(valid_types)}")
        return v

    @field_validator("high_tech_products")
    @classmethod
    def validate_high_tech_products(cls, v):
        total_ratio = sum(p.revenue_ratio for p in v)
        if abs(total_ratio - 100) > 0.01:
            raise ValueError(f"高新产品收入比例之和不等于100%，当前合计 {total_ratio}%")
        return v


# ═══════════════════════════════════════════════
# 板块四：专利/软著申请 (ip_application)
# ═══════════════════════════════════════════════

IP_APPLICATION_STATUSES = [
    "draft",                    # 初始状态，信息不完整
    "materials_collecting",     # 材料收集阶段
    "drafting",                 # 专利/软著撰写中
    "submitting",               # 已提交至专利局/版权中心
    "examination",              # 审查中
    "needs_info",               # 需要补正/答复审查意见（可从任何状态进入）
    "granted",                  # 已授权/登记
    "rejected",                 # 被驳回
]

CAPABILITIES_IP = {
    "status_machine": {
        "initial": "draft",
        "states": IP_APPLICATION_STATUSES,
        "transitions": {
            "draft": ["materials_collecting"],
            "materials_collecting": ["drafting", "needs_info"],
            "drafting": ["submitting", "needs_info"],
            "submitting": ["examination", "needs_info"],
            "examination": ["needs_info", "granted", "rejected"],
            "needs_info": ["materials_collecting", "drafting"],
            "granted": [],
            "rejected": [],
        },
    },
    "agent_auto": {
        "description": "以下判定对方 agent 可独立完成，无需人工介入",
        "items": [
            {"id": "format_check", "name": "格式校验", "detail": "校验申请材料格式、页数、图片清晰度、命名规范等"},
            {"id": "prior_art_search_basic", "name": "基础查新检索", "detail": "对技术关键词进行专利数据库初步检索，评估新颖性"},
            {"id": "claim_structure_check", "name": "权利要求结构检查", "detail": "检查权利要求书的格式是否规范、引用关系是否正确、是否得到说明书支持"},
            {"id": "fee_calculation", "name": "费用自动计算", "detail": "根据申请类型、申请方式、加速审查等自动计算官费和代理费"},
            {"id": "document_completeness", "name": "材料完整性检查", "detail": "逐项检查申请所需材料的提交状态，标记缺失项"},
        ],
    },
    "human_required": {
        "description": "以下事项需要真人介入",
        "items": [
            {"id": "patent_drafting", "name": "专利/软著撰写", "detail": "权利要求书、说明书、摘要等核心文书需要专业代理人撰写"},
            {"id": "examination_response", "name": "审查意见答复", "detail": "专利局/版权中心发出审查意见通知书，需要专利代理人分析并撰写答复意见"},
            {"id": "priority_claim_handling", "name": "优先权处理", "detail": "要求优先权时需要核对优先权文件及翻译件，确保符合时限要求"},
            {"id": "complex_technical_fields", "name": "复杂技术领域处理", "detail": "AI/区块链/生物医药等新兴复杂技术领域需要专业代理人深度理解后撰写"},
            {"id": "foreign_filing", "name": "涉外申请", "detail": "PCT国际申请或直接向外国专利局提交申请，需要涉外专利代理机构处理"},
        ],
    },
    "escalation": {
        "description": "触发转人的条件",
        "trigger_conditions": [
            {"condition": "复杂技术领域", "action": "标记为复杂技术领域 + 转专业代理人撰写 + 暂停自动流程"},
            {"condition": "需要涉外申请", "action": "标记涉外需求 + 转涉外代理机构对接 + 生成费用预估"},
            {"condition": "审查意见答复期限临近", "action": "标记紧急状态 + 输出审查意见分析 + 通知人工优先处理"},
            {"condition": "专利异议/无效宣告", "action": "标记异议/无效程序 + 转专业代理团队 + 暂停正常审查流程"},
        ],
    },
    "knowledge_base": {
        "description": "知识产权类型、时限与费用知识库",
        "ip_types": [
            {
                "type": "invention",
                "name": "发明专利",
                "description": "对产品、方法或者其改进所提出的新的技术方案",
                "protection_years": 20,
                "typical_timeline": "18-36个月（普通），6-18个月（优先审查）",
                "fee_schedule": {"application_fee": 900, "substantive_examination_fee": 2500, "annual_fee_year_1_3": 900, "annual_fee_year_4_6": 1200, "annual_fee_year_7_9": 2000},
            },
            {
                "type": "utility",
                "name": "实用新型专利",
                "description": "对产品的形状、构造或者其结合所提出的适于实用的新的技术方案",
                "protection_years": 10,
                "typical_timeline": "6-12个月",
                "fee_schedule": {"application_fee": 500, "annual_fee_year_1_3": 600, "annual_fee_year_4_5": 900, "annual_fee_year_6_8": 1200},
            },
            {
                "type": "design",
                "name": "外观设计专利",
                "description": "对产品的形状、图案或者其结合以及色彩与形状、图案的结合所作出的富有美感并适于工业应用的新设计",
                "protection_years": 15,
                "typical_timeline": "4-8个月",
                "fee_schedule": {"application_fee": 500, "annual_fee_year_1_3": 600, "annual_fee_year_4_5": 900, "annual_fee_year_6_8": 1200},
            },
            {
                "type": "software_copyright",
                "name": "计算机软件著作权",
                "description": "对计算机软件作品的著作权保护，含源程序及相关文档",
                "protection_years": 50,
                "typical_timeline": "30-60个工作日（普通），15个工作日（加急）",
                "fee_schedule": {"application_fee": 300, "expedited_fee": 500},
            },
        ],
    },
}


class Inventor(BaseModel):
    name: str = Field(..., min_length=1, description="发明人/设计人姓名")
    id_number: str = Field(..., min_length=1, description="身份证号")


class IPApplicationParams(BaseModel):
    # 知识产权类型
    ip_type: str = Field(..., description="知识产权类型: invention（发明专利）/ utility（实用新型）/ design（外观设计）/ software_copyright（软件著作权）")

    # 申请名称
    title: Dict[str, str] = Field(..., description="申请名称，如 {'zh': '一种XXX方法及系统', 'en': 'A method and system for XXX'}")

    # 申请人/权人信息
    applicant_type: str = Field(..., description="申请人类型: company（企业）/ individual（个人）/ joint（共同申请）")
    applicant_name: str = Field(..., min_length=1, description="申请人名称（企业全称或个人姓名）")
    applicant_credit_code: Optional[str] = Field(None, description="统一社会信用代码（企业申请时必填）")
    applicant_id_number: Optional[str] = Field(None, description="身份证号（个人申请时必填）")

    # 发明人/设计人
    inventors: List[Inventor] = Field(..., min_length=1, description="发明人/设计人列表（至少1人）")

    # 联系人
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")

    # 技术内容
    technical_field: str = Field(..., min_length=1, description="所属技术领域")
    abstract: str = Field(..., max_length=1000, description="摘要（中文，1000字以内）")
    claims_text: Optional[str] = Field(None, description="权利要求书全文（发明专利/实用新型必填）")
    description: Optional[str] = Field(None, description="说明书全文（含技术领域、背景技术、发明内容、附图说明、具体实施方式）")

    # 附图
    has_drawings: bool = Field(False, description="是否包含附图")
    drawing_description: Optional[str] = Field(None, description="附图说明（当 has_drawings=True 时推荐填写）")

    # 优先权
    priority_info: Optional[Dict[str, Any]] = Field(None, description="优先权信息，如 {\"app_number\": \"CN202310001234.5\", \"date\": \"2023-01-01\", \"country\": \"中国\"}")

    # 软著专用字段
    source_code_extracts: Optional[str] = Field(None, description="源程序摘录（软件著作权申请时提供，前30页+后30页）")
    user_manual_pages: Optional[int] = Field(None, ge=1, description="用户手册页数（软件著作权申请时提供）")

    # 加急
    is_expedited: bool = Field(False, description="是否加急处理")

    # 备注
    notes: Optional[str] = Field(None, description="补充说明")

    # ── 校验器 ──

    @field_validator("ip_type")
    @classmethod
    def validate_ip_type(cls, v):
        valid_types = {"invention", "utility", "design", "software_copyright"}
        if v not in valid_types:
            raise ValueError(f"无效的知识产权类型: {v}，支持: {', '.join(valid_types)}")
        return v

    @field_validator("applicant_type")
    @classmethod
    def validate_applicant_type(cls, v):
        valid_types = {"company", "individual", "joint"}
        if v not in valid_types:
            raise ValueError(f"无效的申请人类型: {v}，支持: {', '.join(valid_types)}")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if "zh" not in v:
            raise ValueError("标题必须包含中文字段 (zh)")
        if len(v["zh"]) < 4:
            raise ValueError(f"中文标题太短: {v['zh']}，至少4个字符")
        return v

    @field_validator("inventors")
    @classmethod
    def validate_inventors(cls, v):
        if len(v) < 1:
            raise ValueError("至少需要1名发明人/设计人")
        return v

    @field_validator("abstract")
    @classmethod
    def validate_abstract_length(cls, v):
        if len(v) > 1000:
            raise ValueError(f"摘要字数超出限制，当前 {len(v)} 字，最大1000字")
        return v

    @model_validator(mode="after")
    def validate_claims_for_invention_utility(self):
        if self.ip_type in ("invention", "utility") and not self.claims_text:
            raise ValueError("发明专利和实用新型必须提供权利要求书 (claims_text)")
        return self


# ═══════════════════════════════════════════════
# 板块五：进出口备案 (import_export)
# ═══════════════════════════════════════════════

IMPORT_EXPORT_STATUSES = [
    "draft",                        # 初始状态，信息不完整
    "materials_collecting",         # 材料收集阶段
    "customs_registration",         # 海关登记/备案中
    "e_port_registration",          # 电子口岸IC卡办理中
    "foreign_exchange_registration", # 外汇管理局备案中
    "tax_rebate_registration",      # 出口退税备案中
    "needs_info",                   # 需要补充材料（可从任何状态进入）
    "completed",                    # 已完成
    "failed",                       # 任务失败
]

CAPABILITIES_IE = {
    "status_machine": {
        "initial": "draft",
        "states": IMPORT_EXPORT_STATUSES,
        "transitions": {
            "draft": ["materials_collecting"],
            "materials_collecting": ["customs_registration", "needs_info"],
            "customs_registration": ["e_port_registration", "needs_info"],
            "e_port_registration": ["foreign_exchange_registration", "needs_info"],
            "foreign_exchange_registration": ["tax_rebate_registration", "needs_info"],
            "tax_rebate_registration": ["completed", "needs_info"],
            "needs_info": ["materials_collecting", "customs_registration", "e_port_registration", "foreign_exchange_registration", "tax_rebate_registration"],
            "completed": [],
            "failed": [],
        },
    },
    "agent_auto": {
        "description": "以下判定对方 agent 可独立完成，无需人工介入",
        "items": [
            {"id": "document_format_check", "name": "文件格式校验", "detail": "校验文件类型、大小、清晰度，确保符合海关/商务局系统上传要求"},
            {"id": "info_consistency_check", "name": "信息一致性校验", "detail": "核对公司名称、信用代码、经营范围等是否在全部文件中保持一致"},
            {"id": "cross_step_dependency_tracking", "name": "跨步骤依赖追踪", "detail": "前一步骤的审批结果自动触发下一步骤所需材料的准备提醒"},
            {"id": "fee_calculation", "name": "费用自动计算", "detail": "根据备案类型、是否加急、是否委托代办等自动计算各项官费和代理费"},
        ],
    },
    "human_required": {
        "description": "以下事项需要真人介入",
        "items": [
            {"id": "customs_submission", "name": "海关系统提交", "detail": "需登录中国国际贸易单一窗口进行最终提交，CA证书/电子口岸卡签名"},
            {"id": "e_port_card_pickup", "name": "电子口岸卡领取", "detail": "电子口岸IC卡/读卡器需线下领取或快递签收，需专人跟进"},
            {"id": "bank_foreign_exchange_handling", "name": "银行外汇备案办理", "detail": "企业名录登记需到银行柜台办理货物贸易外汇收支企业名录登记"},
            {"id": "customs_officer_communication", "name": "海关官员沟通", "detail": "涉及海关现场查验、商品归类争议、价格质疑等需直接与海关人员沟通"},
        ],
    },
    "escalation": {
        "description": "触发转人的条件",
        "trigger_conditions": [
            {"condition": "特殊商品类别需商检", "action": "标记进出口商品涉及法检/商检品类 + 生成商检要求清单 + 转人工对接检验检疫部门"},
            {"condition": "合规问题（商品归类/许可证）", "action": "标记合规风险 + 输出风险分析报告 + 转人工审核 + 暂停自动流程"},
            {"condition": "关键材料缺失且自行无法补办", "action": "标记缺失材料清单 + 说明补办渠道和预计时间 + 转人工协调加急处理"},
            {"condition": "办理超时", "action": "标记超时状态 + 输出当前卡点分析 + 通知人工催办 + 生成替代方案"},
        ],
    },
    "knowledge_base": {
        "description": "进出口备案流程知识库",
        "step_workflow": [
            {
                "step": 1,
                "name": "海关进出口货物收发货人备案",
                "description": "在中国国际贸易单一窗口办理海关备案，获得海关10位编码",
                "typical_timeline": "1-3个工作日（在线办理）",
                "validity": "长期有效",
                "competent_authority": "注册地海关（企管处/科）",
            },
            {
                "step": 2,
                "name": "电子口岸IC卡办理",
                "description": "申领电子口岸卡（法人卡+操作员卡），用于后续所有电子报关操作",
                "typical_timeline": "3-5个工作日（在线申请+线下领取/快递）",
                "validity": "长期有效（需定期更新证书）",
                "competent_authority": "当地电子口岸数据中心（数据分中心）",
            },
            {
                "step": 3,
                "name": "外汇管理局名录登记",
                "description": "在银行或外管局办理货物贸易外汇收支企业名录登记，获得进出口收付汇资格",
                "typical_timeline": "1-3个工作日（银行端办理）",
                "validity": "长期有效",
                "competent_authority": "注册地银行或国家外汇管理局分局",
            },
            {
                "step": 4,
                "name": "出口退（免）税备案",
                "description": "在电子税务局办理出口退免税备案，获得出口退税申报资格",
                "typical_timeline": "3-7个工作日（需审核）",
                "validity": "长期有效",
                "competent_authority": "主管税务机关",
                "note": "仅限有出口业务且需要退税的企业",
            },
        ],
        "required_documents": {
            "customs_registration": [
                "营业执照副本（加盖公章扫描件）",
                "统一社会信用代码证书（如适用）",
                "对外贸易经营者备案登记表（已取消，仅做提示）",
                "企业公章电子印章",
                "法人身份证正反面扫描件",
                "操作员身份证正反面扫描件",
                "海关报关单位情况登记表",
            ],
            "e_port_registration": [
                "电子口岸企业入网申请表",
                "营业执照副本复印件（加盖公章）",
                "法人身份证复印件",
                "操作员身份证复印件",
                "海关备案证明文件",
                "企业公章、法人章实体印章（线下领取时使用）",
            ],
            "foreign_exchange_registration": [
                "货物贸易外汇收支企业名录登记申请表",
                "营业执照副本原件及复印件",
                "对外贸易经营者备案登记表（如持有）",
                "海关进出口货物收发货人备案回执",
                "企业公章",
                "法人身份证原件（如到柜台办理）",
            ],
            "tax_rebate_registration": [
                "出口退（免）税备案申请表",
                "营业执照副本复印件",
                "海关进出口货物收发货人备案回执复印件",
                "开户银行许可证或基本存款账户信息表",
                "企业公章",
                "增值税一般纳税人资格登记表（如适用）",
            ],
        },
        "typical_timelines": {
            "total_estimated": "2-4周（全流程，不含特殊商品商检）",
            "customs_registration": "1-3个工作日",
            "e_port_registration": "3-5个工作日",
            "foreign_exchange_registration": "1-3个工作日",
            "tax_rebate_registration": "3-7个工作日",
            "note_simultaneous": "海关备案和电子口岸卡办理可以同期进行",
            "note_pickup": "电子口岸卡领取方式分为『线下自取』（当天）和『快递邮寄』（1-3天）",
            "note_bank": "外汇名录登记可在任一具备外汇业务资质的银行办理，建议选择主要结算银行",
        },
        "common_pitfalls": [
            {"issue": "经营范围未包含进出口相关表述", "consequence": "无法办理海关备案", "solution": "先办理经营范围变更，添加『货物进出口；技术进出口』等表述"},
            {"issue": "营业执照注册地址与实际经营地址不一致", "consequence": "海关现场核查无法通过", "solution": "确保营业执照地址真实有效，或办理地址变更"},
            {"issue": "报关负责人未持有报关员资格", "consequence": "部分海关要求报关人员持有报关员证", "solution": "安排公司人员参加报关员考试或委托专业报关行"},
            {"issue": "电子口岸卡办理时法人信息不匹配", "consequence": "电子口岸卡申请被退回", "solution": "核对法人身份证号、姓名与工商登记信息完全一致"},
        ],
    },
}


class ImportExportParams(BaseModel):
    """进出口备案参数模型"""

    # 企业基本信息
    company_name: str = Field(..., min_length=1, description="公司全称（需与营业执照一致）")
    unified_social_credit_code: str = Field(..., min_length=18, max_length=18, description="统一社会信用代码（18位）")

    # 经营范围
    business_scope: str = Field(..., min_length=4, description="经营范围（必须包含进出口相关项目，如『货物进出口』『技术进出口』『进出口代理』等）")
    registered_address: str = Field(..., min_length=4, description="注册地址（需与营业执照完全一致）")

    # 法人信息
    legal_person_name: str = Field(..., min_length=1, description="法定代表人姓名")
    legal_person_phone: str = Field(..., min_length=11, description="法定代表人手机号")

    # 联系人信息
    contact_name: str = Field(..., min_length=1, description="联系人姓名（日常对接人）")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱（接收海关通知等）")

    # 报关负责人
    customs_declaration_person_name: str = Field(..., min_length=1, description="报关负责人姓名")

    # 业务类型
    has_import_business: bool = Field(..., description="是否有进口业务")
    has_export_business: bool = Field(..., description="是否有出口业务")
    main_import_export_products: str = Field(..., min_length=2, description="主要进出口产品（如：电子元器件、机械设备、纺织品等）")

    # 特殊商品
    special_goods_types: Optional[List[str]] = Field(None, description="特殊商品类型，如 hazardous（危险品）/ food（食品/农产品）/ medical（医疗器械/药品）/ chemical（化工品）/ animal_plant（动植物及其产品）/ wood（木制品）/ cosmetic（化妆品）/ other（其他需商检品类）")

    # 业务规模预估
    expected_annual_import_volume_usd: Optional[float] = Field(None, ge=0, description="预计年进口额（美元）")
    expected_annual_export_volume_usd: Optional[float] = Field(None, ge=0, description="预计年出口额（美元）")

    # 所需服务选择
    need_e_port_card: bool = Field(True, description="是否需要办理电子口岸IC卡（默认需要）")
    need_safe_registration: bool = Field(True, description="是否需要外汇管理局名录登记（默认需要）")
    need_export_tax_rebate: bool = Field(False, description="是否需要出口退免税备案（仅出口企业且需退税时勾选）")

    # 已有材料
    existing_documents: Optional[Dict[str, bool]] = Field(
        None,
        description="已有材料情况，如 {'customs_has': False, 'e_port_has': True, 'safe_has': False, 'tax_rebate_has': False}",
    )

    # 备注
    notes: Optional[str] = Field(None, description="补充说明（如特殊需求、时间要求等）")

    # ── 校验器 ──

    @field_validator("unified_social_credit_code")
    @classmethod
    def validate_credit_code(cls, v):
        if len(v) != 18:
            raise ValueError(f"统一社会信用代码必须为18位，当前{v}长度{len(v)}")
        return v

    @field_validator("business_scope")
    @classmethod
    def validate_business_scope_contains_ie(cls, v):
        import_export_keywords = ["进出口", "货物进出口", "技术进出口", "进出口代理", "国际贸易", "外贸"]
        if not any(kw in v for kw in import_export_keywords):
            raise ValueError(
                f"经营范围必须包含进出口相关表述（如：货物进出口、技术进出口、进出口代理等），当前经营范围: {v}"
            )
        return v

    @field_validator("has_import_business", "has_export_business")
    @classmethod
    def validate_at_least_one_business(cls, v, info):
        # 此校验在 model_validator 中统一处理，此处仅通过类型检查
        return v

    @field_validator("special_goods_types")
    @classmethod
    def validate_special_goods_types(cls, v):
        if v is not None:
            valid_types = {"hazardous", "food", "medical", "chemical", "animal_plant", "wood", "cosmetic", "other"}
            for t in v:
                if t not in valid_types:
                    raise ValueError(f"无效的特殊商品类型: {t}，支持: {', '.join(valid_types)}")
        return v

    @model_validator(mode="after")
    def validate_business_type(self):
        if not self.has_import_business and not self.has_export_business:
            raise ValueError("至少需要选择进口业务或出口业务之一")
        return self

    @model_validator(mode="after")
    def validate_special_goods_requires_customs_submission(self):
        if self.special_goods_types:
            # 含特殊商品时自动标记需要海关商检
            pass
        return self


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


# ═══════════════════════════════════════════════
# 板块六：法律咨询 (legal_consulting)
# ═══════════════════════════════════════════════

LEGAL_CONSULTING_STATUSES = [
    "draft",
    "consulting",
    "needs_info",
    "completed",
    "failed",
]

CAPABILITIES_LEGAL = {
    "status_machine": {
        "initial": "draft",
        "states": LEGAL_CONSULTING_STATUSES,
        "transitions": {
            "draft": ["consulting", "needs_info"],
            "consulting": ["needs_info", "completed"],
            "needs_info": ["consulting"],
            "completed": [],
            "failed": [],
        },
    },
    "agent_auto": {
        "description": "以下判定对方 agent 可独立完成",
        "items": [
            {"id": "document_format_check", "name": "文书格式检查", "detail": "检查上传文件的格式、完整性、可读性"},
            {"id": "basic_legal_research", "name": "基础法律检索", "detail": "查找相关法律法规条文和司法解释作为参考"},
            {"id": "deadline_tracking", "name": "期限跟踪提醒", "detail": "诉讼时效、合同到期日、立案期限等关键日期提醒"},
            {"id": "conflict_check", "name": "利益冲突检索", "detail": "检查是否与已有案件存在利益冲突"},
            {"id": "fee_estimation", "name": "费用预估", "detail": "根据案件类型和复杂度估算服务费用"},
        ],
    },
    "human_required": {
        "description": "以下事项需要律师/法务介入",
        "items": [
            {"id": "legal_analysis", "name": "法律分析意见", "detail": "出具法律分析报告，包含风险提示和建议方案"},
            {"id": "document_drafting", "name": "法律文书起草", "detail": "合同、律师函、起诉状、答辩状等法律文书起草"},
            {"id": "contract_review", "name": "合同审查/修订", "detail": "对合同条款进行逐条审查，标注风险并提出修改建议"},
            {"id": "case_strategy", "name": "诉讼策略制定", "detail": "分析案情制定诉讼/仲裁策略"},
            {"id": "negotiation_support", "name": "谈判支持", "detail": "陪同或远程参与商业谈判"},
            {"id": "compliance_audit", "name": "合规审查", "detail": "对企业经营行为进行合规性审查并出具整改建议"},
        ],
    },
    "escalation": {
        "trigger_conditions": [
            {"condition": "涉及刑事犯罪指控", "action": "标记高风险 + 推荐刑事律师团队"},
            {"condition": "跨境法律事务", "action": "标记涉外 + 转涉外法律专家"},
            {"condition": "标的额超过500万", "action": "标记重大案件 + 需合伙人审核 + 推荐高级律师"},
            {"condition": "紧急法律需求（48小时内）", "action": "标记加急 + 优先安排律师"},
            {"condition": "涉及上市公司/公众公司", "action": "标记特殊主体 + 需证券法律师介入"},
        ],
    },
    "knowledge_base": {
        "service_types": [
            {"id": "contract_review", "name": "合同审查/修订", "typical_timeline": "1-3个工作日", "price_range": "500-3000/份"},
            {"id": "legal_advice", "name": "法律咨询", "typical_timeline": "即时-1个工作日", "price_range": "200-1000/次"},
            {"id": "document_drafting", "name": "法律文书起草", "typical_timeline": "2-5个工作日", "price_range": "1000-5000/份"},
            {"id": "litigation_support", "name": "诉讼支持", "typical_timeline": "视案件复杂度", "price_range": "按标的比例或计时收费"},
            {"id": "compliance_review", "name": "合规审查", "typical_timeline": "3-10个工作日", "price_range": "3000-20000/次"},
            {"id": "equity_design", "name": "股权架构设计", "typical_timeline": "5-15个工作日", "price_range": "5000-30000/次"},
        ],
    },
}


class LegalConsultingParams(BaseModel):
    """法律咨询服务参数"""
    service_type: str = Field(..., description="服务类型: contract_review / legal_advice / document_drafting / litigation_support / compliance_review / equity_design")
    company_name: str = Field(..., min_length=1, description="企业名称")
    unified_social_credit_code: Optional[str] = Field(None, min_length=18, max_length=18, description="统一社会信用代码（18位）")

    # 联系人
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")

    # 案件描述
    case_title: str = Field(..., min_length=4, description="案件标题/摘要（如：XX采购合同审查）")
    case_summary: str = Field(..., min_length=10, description="案件详细描述（包含背景、争议焦点、诉求）")
    related_parties: Optional[str] = Field(None, description="相关方信息（对方名称、联系人等）")
    contract_amount: Optional[float] = Field(None, ge=0, description="合同/案件涉及金额（万元）")

    # 附件
    has_uploaded_documents: Optional[bool] = Field(False, description="是否已上传相关文件")
    uploaded_doc_types: Optional[List[str]] = Field(None, description="已上传文件类型列表")

    # 紧急程度
    urgency: str = Field("normal", description="紧急程度: normal / urgent / emergency")
    expected_completion_date: Optional[str] = Field(None, description="期望完成日期（YYYY-MM-DD）")

    # 偏好
    preferred_lawyer_field: Optional[str] = Field(None, description="偏好律师专业领域（如：合同法、劳动法、知识产权法等）")
    budget_range: Optional[str] = Field(None, description="预算范围")
    is_commercial: Optional[bool] = Field(True, description="是否商业用途（个人咨询 vs 企业咨询）")

    notes: Optional[str] = Field(None, description="补充说明")

    @field_validator("service_type")
    @classmethod
    def validate_service_type(cls, v):
        valid_types = ["contract_review", "legal_advice", "document_drafting", "litigation_support", "compliance_review", "equity_design"]
        if v not in valid_types:
            raise ValueError(f"无效服务类型: {v}，支持: {', '.join(valid_types)}")
        return v

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v):
        valid_levels = ["normal", "urgent", "emergency"]
        if v not in valid_levels:
            raise ValueError(f"无效紧急程度: {v}，支持: {', '.join(valid_levels)}")
        return v


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
    "high_tech_application": {
        "name": "高企认定/专精特新",
        "description": "国家高新技术企业认定、专精特新中小企业/小巨人申报。IP审计 -> 财务数据核验 -> 研发比例计算 -> 打分预评估 -> 材料提交 -> 专家评审 -> 答辩辅导。",
        "status": "live",
        "schema_model": HighTechApplicationParams,
        "estimated_days": "90-180（按申报批次）",
        "price_range": "8000-30000（按资质类型）",
        "required_documents": [
            "企业营业执照副本",
            "近三年财务审计报告（含研发费用专项审计）",
            "近三年企业所得税年度纳税申报表",
            "知识产权证书（专利/软著/集成电路布图）",
            "科技人员清单及学历/职称证明",
            "研发项目立项报告及验收文件",
            "高新技术产品（服务）收入专项审计报告",
            "近三年科技成果转化证明材料",
            "研发组织管理水平证明材料",
            "产学研合作协议（如有）",
        ],
        "capabilities": CAPABILITIES_HIGH_TECH,
        "workflow_steps": [
            {"step_id": "ip_audit", "name": "知识产权审计", "order": 1, "agent_auto": True},
            {"step_id": "financial_analysis", "name": "财务数据核验", "order": 2, "agent_auto": True},
            {"step_id": "score_evaluation", "name": "评分预评估", "order": 3, "agent_auto": True},
            {"step_id": "document_preparation", "name": "材料准备", "order": 4, "agent_auto": False, "human_role": "材料编制辅导"},
            {"step_id": "submission", "name": "系统提交", "order": 5, "agent_auto": False, "external_service": "科技部/工信部申报系统"},
            {"step_id": "expert_review", "name": "专家评审/答辩", "order": 6, "agent_auto": False, "human_role": "答辩辅导"},
            {"step_id": "result", "name": "结果公示", "order": 7, "agent_auto": True},
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
    "ip_application": {
        "name": "专利/软著申请",
        "description": "发明专利、实用新型、外观设计、软著申请全流程。查新 -> 撰写 -> 提交 -> 审查答复 -> 授权领证。",
        "status": "live",
        "schema_model": IPApplicationParams,
        "estimated_days": "视类型而定（发明18-36个月，实用新型6-12个月，外观4-8个月，软著30-60个工作日）",
        "price_range": "按需定价（发明专利4500-8000，实用新型2500-4000，外观1500-2500，软著800-1500）",
        "required_documents": [
            "技术交底书（含技术领域、背景技术、发明内容、有益效果、具体实施方式）",
            "已有的在先申请文件（如有优先权要求）",
            "发明人身份证复印件",
            "申请人营业执照或身份证复印件",
            "图纸/流程图（如有）",
            "源程序代码摘录（软著申请）",
            "用户手册（软著申请）",
        ],
        "capabilities": CAPABILITIES_IP,
        "workflow_steps": [
            {"step_id": "technical_disclosure", "name": "技术交底", "order": 1, "agent_auto": True},
            {"step_id": "prior_art_search", "name": "查新检索", "order": 2, "agent_auto": True},
            {"step_id": "patent_drafting", "name": "专利撰写", "order": 3, "agent_auto": False, "human_role": "专利代理人"},
            {"step_id": "document_review", "name": "文件确认", "order": 4, "agent_auto": True},
            {"step_id": "submission", "name": "提交申请", "order": 5, "agent_auto": False, "external_service": "专利电子申请系统/版权中心"},
            {"step_id": "examination", "name": "审查阶段", "order": 6, "agent_auto": False, "human_role": "专利代理人"},
            {"step_id": "grant_or_reject", "name": "授权/驳回", "order": 7, "agent_auto": True},
        ],
    },
    "import_export": {
        "name": "进出口备案",
        "description": "企业进出口经营权备案全流程。海关备案 -> 电子口岸 -> 外汇名录 -> 出口退税，一步到位。含商品归类咨询及特殊品类商检指引。",
        "status": "live",
        "schema_model": ImportExportParams,
        "estimated_days": "14-30",
        "price_range": "800-2500",
        "required_documents": [
            "营业执照副本（加盖公章扫描件）",
            "法人身份证正反面扫描件",
            "操作员身份证正反面扫描件（办理电子口岸卡使用）",
            "企业公章电子印章",
            "开户银行许可证或基本存款账户信息",
            "主要进出口产品清单及HS编码（如有）",
        ],
        "capabilities": CAPABILITIES_IE,
        "workflow_steps": [
            {"step_id": "materials_preparation", "name": "材料收集与审核", "order": 1, "agent_auto": True},
            {"step_id": "customs_registration", "name": "海关备案提交", "order": 2, "agent_auto": False, "external_service": "中国国际贸易单一窗口"},
            {"step_id": "e_port_card", "name": "电子口岸IC卡办理", "order": 3, "agent_auto": False, "human_role": "线下领取/快递签收"},
            {"step_id": "safe_registration", "name": "外汇管理局名录登记", "order": 4, "agent_auto": False, "human_role": "银行柜台办理"},
            {"step_id": "tax_rebate_registration", "name": "出口退免税备案", "order": 5, "agent_auto": False, "external_service": "电子税务局"},
            {"step_id": "confirmation", "name": "完成确认", "order": 6, "agent_auto": True},
        ],
    },
    "legal_consulting": {
        "name": "法律咨询",
        "description": "合同审查、法律咨询、文书起草、诉讼支持、合规审查。律师团队对接，覆盖公司法、合同法、劳动法、知识产权法等常见领域。",
        "status": "live",
        "schema_model": LegalConsultingParams,
        "estimated_days": "视服务类型（1-15个工作日）",
        "price_range": "200-30000（按类型）",
        "required_documents": [
            "合同/文件原件或扫描件（合同审查类）",
            "案情描述及相关证据材料（诉讼支持类）",
            "企业营业执照副本（企业客户）",
            "双方联系方式及背景信息",
        ],
        "capabilities": CAPABILITIES_LEGAL,
        "workflow_steps": [
            {"step_id": "case_intake", "name": "案情收集与分析", "order": 1, "agent_auto": True},
            {"step_id": "lawyer_assignment", "name": "指派律师", "order": 2, "agent_auto": False, "human_role": "案件分配"},
            {"step_id": "legal_research", "name": "法律研究与分析", "order": 3, "agent_auto": False, "human_role": "律师"},
            {"step_id": "deliverable", "name": "交付成果", "order": 4, "agent_auto": False, "human_role": "律师"},
            {"step_id": "review_and_revise", "name": "审核与修订", "order": 5, "agent_auto": True},
            {"step_id": "closure", "name": "结案", "order": 6, "agent_auto": True},
        ],
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


# ── 供应商模型 ──

VALID_SUPPLIER_STATUSES = ["pending", "approved", "rejected"]

class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=1, description="姓名/企业名称")
    phone: str = Field(..., min_length=11, description="手机号")
    wechat: Optional[str] = Field(None, description="微信号")
    city: str = Field(..., min_length=1, description="所在城市")
    service_types: List[str] = Field(..., min_length=1, description="可服务品类")
    id_number: Optional[str] = Field(None, description="身份证号（自然人）/ 信用代码（企业）")
    qualification_desc: Optional[str] = Field(None, description="资质说明")

class SupplierUpdate(BaseModel):
    status: str = Field(..., description="审核状态: approved / rejected")
    notes: Optional[str] = Field(None, description="审核备注")

class SupplierInfo(BaseModel):
    id: int
    name: str
    phone: str
    wechat: Optional[str] = None
    city: str
    service_types: List[str]
    id_number: Optional[str] = None
    qualification_desc: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str

class SupplierListResponse(BaseModel):
    suppliers: List[SupplierInfo]
    total: int


# ── 面板统数据 ──

class DashboardResponse(BaseModel):
    task_counts: Dict[str, int]
    total_tasks: int
    supplier_counts: Dict[str, int]
    total_suppliers: int


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
