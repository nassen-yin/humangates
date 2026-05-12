from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Dict, List
from datetime import datetime

# ═══════════════════════════════════════════════
# 基础模型 (Task models)
# ═══════════════════════════════════════════════

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

# ═══════════════════════════════════════════════
# 共享子模型 (Sub-models)
# ═══════════════════════════════════════════════

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
    id_card_valid_until: Optional[str] = Field(None, description="身份证有效期止（YYYY-MM-DD），长期填'long_term'")
    contribution_method: Optional[str] = Field("货币", description="出资方式：货币 / 实物 / 知识产权 / 土地使用权")
    is_identity_verified: Optional[bool] = Field(False, description="是否已完成工商App实名认证")

class Executive(BaseModel):
    """高管任职信息"""
    role: str = Field(..., description="职务: executive_director / manager / supervisor")
    name: str = Field(..., description="姓名")
    id_number: str = Field(..., description="身份证号")
    tenure: Optional[str] = Field("三年", description="任期年限")

class RegisteredAddress(BaseModel):
    address_type: str = Field(..., description="地址类型: own（自有）/ lease（租赁）/ virtual（园区虚拟地址）")
    address_detail: str = Field(..., min_length=4, description="详细注册地址（精确到门牌号）")
    property_owner_name: Optional[str] = Field(None, description="产权人姓名/名称")
    property_owner_phone: Optional[str] = Field(None, description="产权人联系电话")
    property_cert_number: Optional[str] = Field(None, description="不动产权证号")
    lease_term_years: Optional[int] = Field(None, ge=1, description="租期（年）")
    lease_start_date: Optional[str] = Field(None, description="租赁起始日期（YYYY-MM-DD）")
    is_residential_to_commercial: Optional[bool] = Field(False, description="是否住改商（住宅用作注册地址需居委会盖章）")

class ArticlesOfAssociation(BaseModel):
    profit_distribution_ratio: Optional[str] = Field("按出资比例分配", description="利润分配方式")
    voting_rights_ratio: Optional[str] = Field("按出资比例行使", description="表决权行使方式")
    legal_representative: str = Field(..., description="法定代表人产生方式: 执行董事兼任 / 经理担任 / 董事会选举")
    board_establishment: Optional[str] = Field("不设董事会，设执行董事一名", description="董事会设立方式")
    supervisor_establishment: Optional[str] = Field("不设监事会，设监事一名", description="监事会设立方式")
    capital_contribution_deadline: str = Field(..., description="出资期限（YYYY-MM-DD，新法规定最长5年）")

class BusinessScopeItem(BaseModel):
    code: str = Field(..., description="国民经济行业分类代码（如 I6510）")
    description: str = Field(..., description="经营项目描述")
    is_major: bool = Field(True, description="是否为主营项目")

class BusinessScope(BaseModel):
    industry_category: str = Field(..., description="行业门类（如 I-信息传输、软件和信息技术服务业）")
    items: List[BusinessScopeItem] = Field(..., min_length=1, description="经营项目列表")
    special_items: Optional[List[str]] = Field(None, description="需要前置许可的项目（如食品经营、ICP等）")

# ═══════════════════════════════════════════════
# 板块一·一：公司注册 (company_registration)
# ═══════════════════════════════════════════════

class CompanyRegistrationParams(BaseModel):
    company_names: List[str] = Field(..., min_length=1, max_length=5, description="备选公司名称，至少1个最多5个")
    registered_capital: int = Field(..., ge=1, description="注册资本（万元）")
    capital_currency: str = Field("人民币", description="注册资本币种")
    business_scope: str = Field(..., min_length=4, description="经营范围文字描述")
    business_scope_codes: Optional[List[str]] = Field(None, description="国民经济行业分类代码列表")
    shareholders: List[Shareholder] = Field(..., min_length=1, description="股东信息列表（至少1人，最多50人）")
    executives: Optional[List[Executive]] = Field(None, description="高管任职安排（不填则默认法人为执行董事兼经理，另设一名监事）")
    address: RegisteredAddress
    articles: ArticlesOfAssociation
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    is_all_shareholders_verified: Optional[bool] = Field(False, description="是否所有股东已完成工商App实名认证")
    verification_method: Optional[str] = Field(None, description="实名认证方式: app（工商App）/ face（线下扫脸）/ online（网银认证）")
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
            raise ValueError(f"股东出资比例之和不等于100%，当前{total_pct}%")
        if not any(s.role == "legal_person" for s in v):
            raise ValueError("必须指定一个法人(legal_person)")
        has_supervisor = any(s.role == "supervisor" for s in v)
        if not has_supervisor:
            raise ValueError("必须指定一个监事(supervisor)")
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
                raise ValueError(f"出资期限格式错误: {v.capital_contribution_deadline}，应为YYYY-MM-DD")
        return v

# ═══════════════════════════════════════════════
# 板块一·二：税务登记 (tax_registration)
# ═══════════════════════════════════════════════

class TaxRegistrationParams(BaseModel):
    company_name: str = Field(..., description="公司全称（与营业执照一致）")
    unified_social_credit_code: str = Field(..., description="统一社会信用代码")
    registered_address: str = Field(..., description="注册地址（与营业执照一致）")
    company_phone: str = Field(..., description="公司联系电话")
    taxpayer_type_preference: Optional[str] = Field(None, description="纳税人类型偏好: small（小规模）/ general（一般纳税人）/ not_sure（由AI推荐）")
    estimated_monthly_revenue: float = Field(..., ge=0, description="预估月营业额（万元）")
    export_business: bool = Field(False, description="是否有出口业务")
    tax_breakfast_needs: Optional[str] = Field(None, description="税收优惠需求")
    invoice_type_preference: str = Field(..., description="发票类型: special（专票）/ normal（普票）/ both（都需要）")
    expected_monthly_invoice_count: int = Field(..., ge=0, description="预计月开票量（份）")
    expected_invoice_quota: float = Field(..., ge=0, description="期望发票单张限额（万元）")
    needs_special_invoice: bool = Field(False, description="是否需要增值税专用发票")
    legal_person_name: str = Field(..., description="法定代表人姓名")
    legal_person_phone: Optional[str] = Field(None, description="法定代表人手机号")
    legal_person_id: str = Field(..., description="法定代表人身份证号")
    cfo_name: Optional[str] = Field(None, description="财务负责人姓名")
    cfo_phone: Optional[str] = Field(None, description="财务负责人手机号")
    tax_agent_name: Optional[str] = Field(None, description="办税人姓名")
    tax_agent_phone: Optional[str] = Field(None, description="办税人手机号")
    bank_name: str = Field(..., description="开户行全称")
    account_number: str = Field(..., description="银行账号")
    account_holder: str = Field(..., description="账户名称（通常为公司全称）")
    business_license_date: str = Field(..., description="成立日期（YYYY-MM-DD）")
    registration_authority: str = Field(..., description="登记机关")
    has_ukey: bool = Field(False, description="是否已持有税务UKey")
    e_tax_account: Optional[str] = Field(None, description="电子税务局账号（如有）")
    remarks: Optional[str] = Field(None, description="备注")

    @field_validator("legal_person_phone")
    @classmethod
    def validate_legal_person_phone(cls, v):
        if v and len(v) < 11:
            raise ValueError("法定代表人手机号格式不正确")
        return v

# ═══════════════════════════════════════════════
# 板块一·三：银行开户 (bank_account)
# ═══════════════════════════════════════════════

class BankAccountParams(BaseModel):
    company_name: str = Field(..., description="公司全称（与营业执照一致）")
    unified_social_credit_code: str = Field(..., description="统一社会信用代码")
    registered_address: str = Field(..., description="注册地址")
    business_scope: Optional[str] = Field(None, description="经营范围")
    company_phone: Optional[str] = Field(None, description="公司联系电话")
    account_type: str = Field("basic", description="账户类型: basic（基本户）/ general（一般户）/ special（专户）/ temp（临时户）")
    city: str = Field(..., description="开户城市（如：石家庄）")
    preferred_bank: Optional[str] = Field(None, description="偏好银行（不填由AI推荐）")
    purpose: str = Field(..., description="开户用途: daily/wage/loan/tax/foreign")
    legal_person_can_attend: bool = Field(..., description="法定代表人能否亲自到银行网点办理")
    alternative_method: Optional[str] = Field(None, description="替代方案: on_site_video（上门+远程视频）/ online_video（全程线上）")
    authorized_person_name: Optional[str] = Field(None, description="授权经办人姓名（法人不到场时）")
    authorized_person_id: Optional[str] = Field(None, description="授权经办人身份证号")
    expected_monthly_volume: Optional[float] = Field(None, ge=0, description="预计月流水（万元）")
    expected_monthly_transaction_count: Optional[int] = Field(None, ge=0, description="预计月交易笔数")
    expected_daily_cash_deposit: Optional[float] = Field(None, ge=0, description="预计日现金存取（万元）")
    has_foreign_currency_needs: bool = Field(False, description="是否有外币业务需求")
    expected_wage_count: Optional[int] = Field(None, ge=0, description="预计代发工资人数")
    needs_pos: bool = Field(False, description="是否需要POS机")
    needs_online_banking: bool = Field(True, description="是否需要网银")
    needs_corporate_wechat_payment: bool = Field(False, description="是否需要企业微信收款")
    urgency: str = Field("normal", description="加急程度: urgent / normal")
    preferred_time: Optional[str] = Field(None, description="期望办理时间")
    existing_accounts: Optional[str] = Field(None, description="已开立银行账户情况")
    remarks: Optional[str] = Field(None, description="备注")

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v):
        if v not in ("urgent", "normal"):
            raise ValueError("urgency必须为urgent或normal")
        return v

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v):
        valid = ("basic", "general", "special", "temp")
        if v not in valid:
            raise ValueError(f"账户类型无效: {v}")
        return v

# ═══════════════════════════════════════════════
# 板块一·四：代理记账 (accounting)
# ═══════════════════════════════════════════════

class AccountingParams(BaseModel):
    company_name: str = Field(..., description="公司全称（与营业执照一致）")
    unified_social_credit_code: str = Field(..., description="统一社会信用代码")
    taxpayer_type: str = Field(..., description="纳税人类型: small（小规模）/ general（一般纳税人）")
    industry: Optional[str] = Field(None, description="所属行业")
    registered_capital: Optional[float] = Field(None, ge=0, description="注册资本（万元）")
    monthly_ticket_count: Optional[int] = Field(None, ge=0, description="月均开票量（份）")
    monthly_revenue: Optional[float] = Field(None, ge=0, description="月均营收（万元）")
    has_previous_accounting: bool = Field(False, description="是否有之前的做账记录")
    previous_accountant_firm: Optional[str] = Field(None, description="之前的代账公司名称")
    preferred_tax_cycle: Optional[str] = Field("monthly", description="报税周期: monthly（月报）/ quarterly（季报）")
    tax_software_familiarity: Optional[str] = Field(None, description="税务软件熟悉程度: none/basic/proficient")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    has_ukey: bool = Field(False, description="是否已有税务UKey")
    need_physical_invoice: bool = Field(False, description="是否需要纸质发票代开")
    need_annual_audit: bool = Field(False, description="是否需要年度审计")
    notes: Optional[str] = Field(None, description="补充说明")

# ═══════════════════════════════════════════════
# 板块一·五：高新技术企业认定 (high_tech_application)
# ═══════════════════════════════════════════════

class HighTechApplicationParams(BaseModel):
    company_name: str = Field(..., description="公司全称")
    unified_social_credit_code: str = Field(..., description="统一社会信用代码")
    registered_capital: float = Field(..., ge=0, description="注册资本（万元）")
    establishment_date: str = Field(..., description="成立日期（YYYY-MM-DD，需满一年以上）")
    industry: str = Field(..., description="行业领域: 电子信息/生物与新医药/航空航天/新材料/高技术服务/新能源与节能/资源与环境/先进制造与自动化")
    core_technology: str = Field(..., description="核心技术描述")
    has_independent_ip: bool = Field(..., description="是否拥有自主知识产权")
    ip_list: Optional[List[str]] = Field(None, description="已有知识产权列表")
    rd_expense_last_year: float = Field(..., ge=0, description="上年度研发费用（万元）")
    revenue_last_year: float = Field(..., ge=0, description="上年度总收入（万元）")
    revenue_last_three_years: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="近三年营收（万元）")
    total_employees: int = Field(..., ge=0, description="员工总数")
    rd_staff_count: int = Field(..., ge=0, description="研发人员数")
    rd_staff_ratio: Optional[float] = Field(None, ge=0, le=100, description="研发人员占比（%）")
    high_new_tech_product_revenue: Optional[float] = Field(None, ge=0, description="高新产品/服务收入（万元）")
    has_internal_rd_management_system: bool = Field(False, description="是否有内部研发管理制度")
    has_rd_expense_ledger: bool = Field(False, description="是否有研发费用辅助账")
    has_quality_management_system: bool = Field(False, description="是否有质量体系认证（ISO等）")
    preferred_district: Optional[str] = Field(None, description="申请地区")
    is_first_application: bool = Field(True, description="是否首次申请")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    notes: Optional[str] = Field(None, description="补充说明")

    @field_validator("establishment_date")
    @classmethod
    def validate_establishment_date(cls, v):
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError(f"成立日期格式错误: {v}")
        return v

    @field_validator("industry")
    @classmethod
    def validate_industry(cls, v):
        valid = ["电子信息", "生物与新医药", "航空航天", "新材料", "高技术服务", "新能源与节能", "资源与环境", "先进制造与自动化"]
        if v not in valid:
            raise ValueError(f"行业领域无效: {v}")
        return v

# ═══════════════════════════════════════════════
# 板块一·六：专利/软著申请 (ip_application)
# ═══════════════════════════════════════════════

class IPApplicationParams(BaseModel):
    ip_type: str = Field(..., description="知识产权类型: invention（发明）/ utility（实用新型）/ design（外观设计）/ software（软著）")
    ip_name: str = Field(..., min_length=2, description="发明/软著名称")
    technical_field: str = Field(..., description="技术领域")
    background_technology: str = Field(..., description="背景技术")
    invention_content: str = Field(..., description="发明/设计内容")
    beneficial_effects: Optional[str] = Field(None, description="有益效果")
    implementation_method: Optional[str] = Field(None, description="具体实施方式")
    applicant_name: str = Field(..., description="申请人名称")
    applicant_type: str = Field(..., description="申请人类型: company/individual/institution")
    applicant_id: str = Field(..., description="申请人证件号")
    applicant_address: str = Field(..., description="申请人地址")
    applicant_postal_code: Optional[str] = Field(None, description="申请人邮编")
    inventor_names: List[str] = Field(..., min_length=1, description="发明人/设计人列表")
    has_drawings: bool = Field(False, description="是否包含图纸/流程图")
    drawing_descriptions: Optional[List[str]] = Field(None, description="图纸说明")
    has_priority_claim: bool = Field(False, description="是否要求优先权")
    priority_country: Optional[str] = Field(None, description="优先权国家")
    priority_date: Optional[str] = Field(None, description="优先权日（YYYY-MM-DD）")
    priority_application_number: Optional[str] = Field(None, description="优先权申请号")
    source_code_excerpt: Optional[str] = Field(None, description="源程序代码摘录（软著）")
    user_manual_summary: Optional[str] = Field(None, description="用户手册摘要（软著）")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    urgency: str = Field("normal", description="加急程度: urgent / normal")
    notes: Optional[str] = Field(None, description="补充说明")

# ═══════════════════════════════════════════════
# 板块一·七：进出口备案 (import_export)
# ═══════════════════════════════════════════════

class ImportExportParams(BaseModel):
    company_name: str = Field(..., description="公司全称")
    unified_social_credit_code: str = Field(..., description="统一社会信用代码")
    registered_address: str = Field(..., description="注册地址")
    english_name: Optional[str] = Field(None, description="公司英文名称")
    registered_capital: float = Field(..., ge=0, description="注册资本（万元）")
    business_scope: str = Field(..., description="经营范围（需包含进出口相关描述）")
    has_import_business: bool = Field(False, description="是否需要进口业务")
    has_export_business: bool = Field(False, description="是否需要出口业务")
    main_products_category: str = Field(..., description="主要进出口产品类别")
    main_trading_countries: List[str] = Field(..., min_length=1, description="主要贸易国家/地区列表")
    legal_person_name: str = Field(..., description="法定代表人姓名")
    legal_person_id: str = Field(..., description="法定代表人身份证号")
    legal_person_phone: Optional[str] = Field(None, description="法定代表人手机号")
    customs_contact_name: Optional[str] = Field(None, description="海关业务联系人姓名")
    customs_contact_phone: Optional[str] = Field(None, description="海关业务联系人手机号")
    customs_contact_email: Optional[str] = Field(None, description="海关业务联系人邮箱")
    has_customs_declarer: bool = Field(False, description="是否有自有报关员")
    needs_declaration_agent: bool = Field(True, description="是否需要代理报关服务")
    needs_foreign_trade_record: bool = Field(True, description="是否需要对外贸易经营者备案")
    needs_customs_registration: bool = Field(True, description="是否需要海关报关单位注册登记")
    needs_electron_port_ic_card: bool = Field(True, description="是否需要电子口岸IC卡/法人卡")
    needs_foreign_exchange_record: bool = Field(True, description="是否需要外汇管理局名录登记")
    needs_tax_refund: bool = Field(False, description="是否需要出口退税备案")
    has_letter_of_credit: bool = Field(False, description="是否有信用证业务需求")
    estimated_annual_import_volume: Optional[float] = Field(None, ge=0, description="预估年进口额（万美元）")
    estimated_annual_export_volume: Optional[float] = Field(None, ge=0, description="预估年出口额（万美元）")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    urgency: str = Field("normal", description="加急程度: urgent / normal")
    notes: Optional[str] = Field(None, description="补充说明")

# ═══════════════════════════════════════════════
# 板块一·八：法律咨询 (legal_consulting)
# ═══════════════════════════════════════════════

class LegalConsultingParams(BaseModel):
    consulting_type: str = Field(..., description="咨询类型: contract_review/agreement_draft/dispute/labor/IP/compliance/investment/other")
    case_title: str = Field(..., min_length=4, description="案件/问题标题")
    case_description: str = Field(..., min_length=20, description="详细描述问题事实背景")
    involved_amount: Optional[float] = Field(None, ge=0, description="涉及金额（万元）")
    opposite_party: Optional[str] = Field(None, description="对方当事人名称")
    has_contract: bool = Field(False, description="是否有已签署合同/协议")
    contract_summary: Optional[str] = Field(None, description="合同关键条款摘要")
    urgency: str = Field("normal", description="紧急程度: urgent/within_week/normal/no_rush")
    has_lawsuits: bool = Field(False, description="是否已涉及诉讼/仲裁")
    court_name: Optional[str] = Field(None, description="管辖法院/仲裁机构（如已立案）")
    case_number: Optional[str] = Field(None, description="案号（如已立案）")
    consulting_goal: str = Field(..., description="咨询目标: risk_analysis/strategy/document/mediation/litigation")
    industry: Optional[str] = Field(None, description="所属行业")
    location: str = Field(..., description="所在地（城市）")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    notes: Optional[str] = Field(None, description="补充说明")

# ═══════════════════════════════════════════════
# 板块一·九：资质代办 (license_application)
# ═══════════════════════════════════════════════

class LicenseApplicationParams(BaseModel):
    license_type: str = Field(..., description="资质类型: icp/food_operation/medical_device/publication/wangwenwang/hygiene/transport/performance/labor_dispatch/hr_service/dangerous_chemicals/radio_tv/other")
    company_name: str = Field(..., description="公司全称")
    unified_social_credit_code: str = Field(..., description="统一社会信用代码")
    registered_capital: float = Field(..., ge=0, description="注册资本（万元）")
    establishment_date: str = Field(..., description="成立日期（YYYY-MM-DD）")
    business_scope: str = Field(..., description="现有经营范围")
    staffing_count: int = Field(..., ge=0, description="员工人数")
    office_area: Optional[float] = Field(None, ge=0, description="办公面积（平方米）")
    capital_reserve: Optional[float] = Field(None, ge=0, description="实缴资本/资金储备（万元）")
    needs_capital_verification: bool = Field(False, description="是否需要验资报告")
    has_historical_application: bool = Field(False, description="之前是否申请过该资质")
    previous_application_result: Optional[str] = Field(None, description="上次申请结果")
    has_penalty_record: bool = Field(False, description="是否有行政处罚记录")
    penalty_detail: Optional[str] = Field(None, description="处罚详情")
    urgency: str = Field("normal", description="加急程度: urgent / normal")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    notes: Optional[str] = Field(None, description="补充说明")

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v):
        if v not in ("urgent", "normal"):
            raise ValueError("urgency必须为urgent或normal")
        return v

# ═══════════════════════════════════════════════
# 板块一·十：商标注册 (trademark)
# ═══════════════════════════════════════════════

class TrademarkParams(BaseModel):
    trademark_type: str = Field(..., description="商标类型: word/design/composite/sound/three_d/color")
    trademark_name: Optional[str] = Field(None, description="商标名称（文字商标必填）")
    trademark_description: Optional[str] = Field(None, description="商标描述（图形/声音/三维商标必填）")
    trademark_design_image: Optional[str] = Field(None, description="商标图样下载地址或base64")
    application_type: str = Field("new", description="业务类型: new/renewal/transfer/change/license/objection/dispute")
    previous_registration_number: Optional[str] = Field(None, description="原注册号（续展/转让/变更时必填）")
    international_classes: str = Field(..., description="尼斯分类编号（逗号分隔，如9,35,42）")
    class_descriptions: Optional[Dict[str, str]] = Field(None, description="各分类商品/服务项目描述")
    total_class_count: int = Field(..., ge=1, le=45, description="申请分类总数（1-45）")
    applicant_type: str = Field(..., description="申请人类型: company/individual/foreign")
    applicant_name: str = Field(..., description="申请人名称（与营业执照一致）")
    applicant_address: str = Field(..., description="申请人地址")
    applicant_id_number: str = Field(..., description="申请人证件号")
    applicant_contact_phone: Optional[str] = Field(None, description="申请人联系电话")
    applicant_contact_email: Optional[str] = Field(None, description="申请人邮箱")
    applicant_postal_code: Optional[str] = Field(None, description="申请人邮编")
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    has_prior_art_search: bool = Field(False, description="是否已进行商标查新检索")
    prior_art_search_report: Optional[str] = Field(None, description="查新检索报告摘要")
    has_priority_claim: bool = Field(False, description="是否主张优先权")
    priority_country: Optional[str] = Field(None, description="优先权国家/地区")
    priority_date: Optional[str] = Field(None, description="优先权日期（YYYY-MM-DD）")
    priority_application_number: Optional[str] = Field(None, description="优先权申请号")
    power_of_attorney_method: str = Field("electronic", description="委托书方式: electronic/paper")
    has_use_intention: bool = Field(True, description="是否具有使用意图")
    use_intention_description: Optional[str] = Field(None, description="使用意图说明")
    urgency: str = Field("normal", description="加急程度: urgent / normal")
    notes: Optional[str] = Field(None, description="补充说明")

    @field_validator("total_class_count")
    @classmethod
    def validate_class_count(cls, v, info):
        classes = info.data.get("international_classes", "")
        if classes:
            count = len([c for c in classes.split(",") if c.strip()])
            if count != v:
                raise ValueError(f"分类数量不一致: 输入{count}个，声明{v}个")
        if v < 1 or v > 45:
            raise ValueError("分类数量必须介于1-45之间")
        return v

    @field_validator("international_classes")
    @classmethod
    def validate_international_classes(cls, v):
        if not v.strip():
            raise ValueError("尼斯分类编号不能为空")
        for p in v.split(","):
            p = p.strip()
            if not p.isdigit() or int(p) < 1 or int(p) > 45:
                raise ValueError(f"无效的分类编号: {p}")
        return v

    @field_validator("trademark_type")
    @classmethod
    def validate_trademark_type(cls, v):
        valid = ("word", "design", "composite", "sound", "three_d", "color")
        if v not in valid:
            raise ValueError(f"商标类型无效: {v}")
        return v

# ═══════════════════════════════════════════════
# 板块一·十一：工商变更 (company_change) — 子模型
# ═══════════════════════════════════════════════

class ShareholderChange(BaseModel):
    """股权/股东变更详情"""
    change_type: str = Field(..., description="变更类型: share_transfer（转让）/ capital_increase（增资）/ capital_decrease（减资）/ share_withdrawal（退股）")
    old_shareholder_name: Optional[str] = Field(None, description="原股东姓名（转让/退股时必填）")
    old_shareholder_id: Optional[str] = Field(None, description="原股东证件号")
    new_shareholder_name: str = Field(..., description="新股东姓名或名称")
    new_shareholder_id: str = Field(..., description="新股东证件号")
    new_shareholder_type: str = Field("individual", description="新股东类型: individual/company")
    transferred_percentage: float = Field(..., ge=0, le=100, description="转让出资比例（%）")
    transferred_capital: float = Field(..., ge=0, description="转让出资额（万元）")
    transfer_price: float = Field(0, ge=0, description="转让价格（万元），0为无偿转让")
    role: str = Field("shareholder", description="职务: shareholder/legal_person")

class ExecutiveChange(BaseModel):
    """高管变更详情"""
    role: str = Field(..., description="职务: legal_representative/executive_director/manager/supervisor")
    old_name: Optional[str] = Field(None, description="原任姓名")
    new_name: str = Field(..., description="新任姓名")
    new_id_number: str = Field(..., description="新任身份证号")
    new_phone: Optional[str] = Field(None, description="新任手机号")
    tenure: str = Field("三年", description="任期")
    change_reason: str = Field("改选", description="变更原因: 改选/辞职/罢免/届满")

# ═══════════════════════════════════════════════
# 板块一·十一：工商变更 (company_change) — 主模型
# ═══════════════════════════════════════════════

class CompanyChangeParams(BaseModel):
    company_name: str = Field(..., description="公司全称（与营业执照一致）")
    unified_social_credit_code: str = Field(..., description="统一社会信用代码")
    registered_district: Optional[str] = Field(None, description="当前注册区域（如：石家庄市长安区）")
    change_types: List[str] = Field(..., min_length=1, description="变更事项: company_name/address/legal_representative/registered_capital/business_scope/shareholder/executive/articles/contact_person")

    # 名称变更
    new_company_name: Optional[str] = Field(None, description="新公司名称")
    name_change_reason: Optional[str] = Field(None, description="名称变更原因")

    # 地址变更
    new_address: str = Field("", min_length=4, description="新注册地址（不涉及地址变更则填空）")
    new_address_property_type: Optional[str] = Field(None, description="新地址类型: own/lease/virtual")
    new_address_owner_name: Optional[str] = Field(None, description="新地址产权人姓名")
    new_address_owner_phone: Optional[str] = Field(None, description="新地址产权人电话")
    new_address_lease_period: Optional[int] = Field(None, ge=1, description="新地址租期（年）")
    new_address_property_cert: Optional[str] = Field(None, description="新地址不动产权证号")
    is_cross_district: Optional[bool] = Field(None, description="是否跨区迁移")
    old_district: Optional[str] = Field(None, description="迁出区")
    new_district: Optional[str] = Field(None, description="迁入区")

    # 法人变更
    old_legal_representative_name: Optional[str] = Field(None, description="原法定代表人姓名")
    old_legal_representative_id: Optional[str] = Field(None, description="原法定代表人身份证号")
    new_legal_representative_name: Optional[str] = Field(None, description="新法定代表人姓名")
    new_legal_representative_id: Optional[str] = Field(None, description="新法定代表人身份证号")
    new_legal_representative_phone: Optional[str] = Field(None, description="新法定代表人手机号")
    old_legal_rep_role_after: Optional[str] = Field(None, description="原法定代表人卸任后: shareholder/none")

    # 注册资本变更
    capital_change_type: Optional[str] = Field(None, description="变更类型: increase（增资）/ decrease（减资）")
    old_registered_capital: Optional[float] = Field(None, ge=0, description="原注册资本（万元）")
    new_registered_capital: Optional[float] = Field(None, ge=0, description="新注册资本（万元）")
    capital_change_method: Optional[str] = Field(None, description="增资方式: money/property/IP/equity 或减资退回方式")
    has_reduction_notice: Optional[bool] = Field(None, description="减资是否已发布公告")
    reduction_notice_proof: Optional[str] = Field(None, description="减资公告证明（报纸/网站/截图）")

    # 经营范围变更
    new_business_scope: Optional[str] = Field(None, description="变更后经营范围全文")
    added_business_items: Optional[List[str]] = Field(None, description="新增经营项目")
    removed_business_items: Optional[List[str]] = Field(None, description="删除的经营项目")
    has_pre_license_items: Optional[bool] = Field(None, description="是否涉及前置许可项目")
    pre_license_status: Optional[str] = Field(None, description="前置许可办理状态")

    # 股东变更
    shareholder_changes: Optional[List[ShareholderChange]] = Field(None, description="股东/股权变更详情")
    updated_total_capital: Optional[float] = Field(None, ge=0, description="变更后总注册资本（万元）")
    updated_shareholder_count: Optional[int] = Field(None, ge=1, description="变更后股东总人数")

    # 高管变更
    executive_changes: Optional[List[ExecutiveChange]] = Field(None, description="高管变更详情")

    # 章程备案
    has_articles_update: Optional[bool] = Field(False, description="是否涉及章程修订")
    articles_update_summary: Optional[str] = Field(None, description="章程修订摘要")

    # 联络人员变更
    new_contact_person_name: Optional[str] = Field(None, description="新工商联络员姓名")
    new_contact_person_phone: Optional[str] = Field(None, description="新工商联络员手机号")
    new_financial_contact_name: Optional[str] = Field(None, description="新财务负责人姓名")
    new_financial_contact_phone: Optional[str] = Field(None, description="新财务负责人手机号")

    # 决议签署
    meeting_type: Optional[str] = Field(None, description="决议类型: shareholders/board/sole")
    is_all_signatories_agree: Optional[bool] = Field(False, description="是否全体股东/董事已同意")
    disagree_shareholders: Optional[List[str]] = Field(None, description="持反对意见的股东姓名")
    signing_method: str = Field("e_sign", description="签署方式: e_sign/offline")

    # 联系人
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")

    # 附加
    urgency: str = Field("normal", description="加急程度: urgent/normal")
    need_license_mail: Optional[bool] = Field(False, description="是否需要邮寄新执照")
    license_mail_address: Optional[str] = Field(None, description="执照邮寄地址")
    notes: Optional[str] = Field(None, description="补充说明")

    @field_validator("change_types")
    @classmethod
    def validate_change_types(cls, v):
        valid = {"company_name", "address", "legal_representative", "registered_capital", "business_scope", "shareholder", "executive", "articles", "contact_person"}
        for t in v:
            if t not in valid:
                raise ValueError(f"无效的变更事项: {t}")
        if "legal_representative" in v and "executive" in v:
            raise ValueError("法人变更已包含高管变更，不需要单独提交executive")
        return v

    @field_validator("new_address")
    @classmethod
    def validate_address_change(cls, v, info):
        change_types = info.data.get("change_types", [])
        if "address" in change_types and not v:
            raise ValueError("地址变更时新地址不能为空")
        if "address" not in change_types and v:
            raise ValueError("未选地址变更，不应填写新地址")
        return v

    @field_validator("capital_change_type")
    @classmethod
    def validate_capital_change_type(cls, v, info):
        if "registered_capital" in info.data.get("change_types", []) and not v:
            raise ValueError("注册资本变更时需指定increase或decrease")
        return v

    @field_validator("reduction_notice_proof")
    @classmethod
    def validate_reduction_notice(cls, v, info):
        if info.data.get("capital_change_type") == "decrease" and not v:
            raise ValueError("减资必须提供公告证明")
        return v


# ═══════════════════════════════════════════════
# 板块能力模型 (CAPABILITIES)
# ═══════════════════════════════════════════════

# ── 公司注册 ──

CAPABILITIES_COMPANY_REGISTRATION = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收客户需求，等待AI预填"},
            {"id": "name_submitted", "name": "核名提交", "description": "已提交至核名系统"},
            {"id": "name_approved", "name": "核名通过", "description": "公司名称预核准通过"},
            {"id": "materials_preparing", "name": "材料准备", "description": "AI生成注册材料（章程、股东会决议、任职文件等）"},
            {"id": "e_sign_pending", "name": "待签署", "description": "e签宝待签署"},
            {"id": "submitted", "name": "已提交", "description": "材料已提交至市场监督管理局"},
            {"id": "in_review", "name": "审核中", "description": "市场监督管理局审核中"},
            {"id": "correction_needed", "name": "补正", "description": "需补充材料"},
            {"id": "approved", "name": "审核通过", "description": "准予设立登记"},
            {"id": "license_collected", "name": "执照领取", "description": "营业执照已领取"},
            {"id": "seal_completed", "name": "刻章完成", "description": "公章、财务章、法人章已刻制"},
            {"id": "completed", "name": "已完成", "description": "全部完成"},
        ],
        "transitions": [
            ["draft", "name_submitted"], ["name_submitted", "name_approved"],
            ["name_approved", "materials_preparing"], ["materials_preparing", "e_sign_pending"],
            ["e_sign_pending", "submitted"], ["submitted", "in_review"],
            ["in_review", "correction_needed"], ["correction_needed", "in_review"],
            ["in_review", "approved"], ["approved", "license_collected"],
            ["license_collected", "seal_completed"], ["seal_completed", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "form_auto_fill", "name": "自动填表", "description": "AI根据用户提供信息自动填充工商注册申请表"},
        {"id": "name_recommendation", "name": "名称推荐", "description": "根据行业和偏好推荐可用公司名称"},
        {"id": "document_generation", "name": "文书生成", "description": "自动生成公司章程、股东会决议、任职文件等"},
        {"id": "material_check", "name": "材料预审", "description": "自动检查材料完整性"},
        {"id": "timeline_calc", "name": "时限预估", "description": "预估全流程办理时限"},
        {"id": "fee_calc", "name": "费用明细", "description": "计算注册总费用"},
        {"id": "progress_push", "name": "进度推送", "description": "实时推送办理进度"},
    ],
    "human_required": [
        {"id": "e_sign_invite", "name": "e签宝发起", "description": "在e签宝系统发起签署流程"},
        {"id": "government_submit", "name": "工商提交", "description": "线上/线下提交至市场监督管理局"},
        {"id": "license_pickup", "name": "执照领取", "description": "到窗口领取营业执照"},
        {"id": "seal_making", "name": "刻章协调", "description": "对接刻章点刻制公章"},
    ],
    "escalation_conditions": [
        {"condition": "name_rejected_3_times", "description": "核名被驳回3次以上"},
        {"condition": "special_industry", "description": "涉及前置许可行业"},
        {"condition": "foreign_investment", "description": "外资企业注册"},
    ],
    "knowledge_base": {
        "legal_basis": ["《公司法》（2024修订）", "《市场主体登记管理条例》"],
        "required_docs": ["公司章程", "股东会决议", "任职文件", "住所使用证明", "股东身份证复印件"],
        "timeline": {"核名": "1个工作日", "材料准备": "1-2个工作日", "工商审核": "3-5个工作日", "刻章": "1个工作日"},
        "faq": [
            {"q": "注册公司需要多少钱？", "a": "基础套餐499元（含核名+材料+提交），刻章200元（自选），银行开户299元（另购）。市场价699-1299元。"},
            {"q": "多长时间能办好？", "a": "核名当天→材料准备1-2天→工商审核3-5天→刻章1天。总计7-14天。"},
            {"q": "法人需要到场吗？", "a": "不需要，e签宝远程签名即可。"},
        ],
    },
}

# ── 税务登记 ──

CAPABILITIES_TAX_REGISTRATION = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收需求"},
            {"id": "forms_prepared", "name": "表单预填", "description": "AI已预填税务登记表单"},
            {"id": "documents_ready", "name": "材料就绪", "description": "材料已准备齐全"},
            {"id": "submitted", "name": "已提交税务局", "description": "已提交至税务局"},
            {"id": "tax_type_assessment", "name": "税种核定", "description": "税种核定中"},
            {"id": "invoice_quota_pending", "name": "发票限额核定", "description": "发票限额审批中"},
            {"id": "ukey_delivery_pending", "name": "UKey发放", "description": "税务UKey发放中"},
            {"id": "completed", "name": "已完成", "description": "税务登记全部完成"},
        ],
        "transitions": [
            ["draft", "forms_prepared"], ["forms_prepared", "documents_ready"],
            ["documents_ready", "submitted"], ["submitted", "tax_type_assessment"],
            ["tax_type_assessment", "invoice_quota_pending"],
            ["invoice_quota_pending", "ukey_delivery_pending"],
            ["ukey_delivery_pending", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "form_auto_fill", "name": "表单自动填写", "description": "根据已填信息自动填充税务登记表"},
        {"id": "taxpayer_type_analysis", "name": "纳税人类型推荐", "description": "根据营收和行业推荐小规模或一般纳税人"},
        {"id": "document_checklist_gen", "name": "材料清单生成", "description": "生成所需材料清单"},
        {"id": "timeline_calc", "name": "时限预估", "description": "预估办理时限"},
        {"id": "progress_push", "name": "进度推送", "description": "实时推送进度"},
        {"id": "deadline_reminder", "name": "截止日提醒", "description": "提醒申报截止日期"},
    ],
    "human_required": [
        {"id": "bureau_submit", "name": "现场提交", "description": "到税务局窗口提交材料"},
        {"id": "ukey_pickup", "name": "UKey领取", "description": "领取税务UKey"},
        {"id": "officer_communication", "name": "税务专管员沟通", "description": "与税务专管员沟通核定事宜"},
    ],
    "escalation_conditions": [
        {"condition": "revenue_over_5M", "description": "预估月营收超过500万元"},
        {"condition": "special_industry", "description": "特殊行业（金融/房地产/外资）"},
        {"condition": "export_business", "description": "有出口业务需出口退税"},
        {"condition": "historical_tax_issues", "description": "有历史税务问题"},
    ],
    "knowledge_base": {
        "legal_basis": ["《税收征收管理法》"],
        "taxpayer_types": [
            {"type": "小规模纳税人", "rate": "3%（减按1%）", "revenue_limit": "年500万以下"},
            {"type": "一般纳税人", "rate": "13%/9%/6%", "revenue_limit": "年500万以上或申请"},
        ],
        "faq": [
            {"q": "小规模和一般纳税人选哪个？", "a": "年营收500万以下选小规模（税率低），500万以上需强制转一般纳税人。如果客户都要专票抵扣，建议直接申请一般纳税人。"},
        ],
    },
}

# ── 银行开户 ──

CAPABILITIES_BANK_ACCOUNT = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收开户需求"},
            {"id": "bank_selected", "name": "银行推荐", "description": "AI推荐最优银行方案"},
            {"id": "appointment_made", "name": "预约成功", "description": "已预约银行办理"},
            {"id": "documents_ready", "name": "材料就绪", "description": "开户材料已准备齐全"},
            {"id": "on_site_visit", "name": "上门核实", "description": "银行客户经理上门核实"},
            {"id": "account_activated", "name": "账户激活", "description": "账户已开通"},
            {"id": "online_banking_setup", "name": "网银开通", "description": "网银/U盾已开通"},
            {"id": "completed", "name": "已完成", "description": "开户全部完成"},
        ],
        "transitions": [
            ["draft", "bank_selected"], ["bank_selected", "appointment_made"],
            ["appointment_made", "documents_ready"], ["documents_ready", "on_site_visit"],
            ["on_site_visit", "account_activated"], ["account_activated", "online_banking_setup"],
            ["online_banking_setup", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "bank_smart_recommend", "name": "智能推荐银行", "description": "根据预算、法人到场情况、业务需求推荐最优银行"},
        {"id": "document_checklist_gen", "name": "材料清单", "description": "生成所需材料清单"},
        {"id": "fee_calc", "name": "费用估算", "description": "估算开户及年费"},
        {"id": "reminder_push", "name": "提醒推送", "description": "办理前提醒"},
        {"id": "material_pre_review", "name": "材料预审", "description": "AI预检材料完整性"},
        {"id": "progress_tracking", "name": "进度跟踪", "description": "跟踪办理进度"},
    ],
    "human_required": [
        {"id": "bank_coordination", "name": "银行对接", "description": "与银行客户经理沟通协调"},
        {"id": "on_site_accompaniment", "name": "现场陪同", "description": "陪同法人到银行办理"},
        {"id": "seal_card_delivery", "name": "印章卡寄送", "description": "安排印章卡寄送"},
    ],
    "escalation_conditions": [
        {"condition": "cannot_attend_no_remote", "description": "法人不能到场且银行不支持远程"},
        {"condition": "special_industry_kyc", "description": "特殊行业KYC审核严格"},
        {"condition": "foreign_currency", "description": "涉及外币业务"},
    ],
    "knowledge_base": {
        "banks_comparison": [
            {"bank": "国有四大行", "attendance": "必须法人到场", "suitable": "大额流水企业"},
            {"bank": "招商/平安", "attendance": "可上门核实", "suitable": "中小企业"},
            {"bank": "网商/微众", "attendance": "全程在线", "suitable": "纯线上小微企业"},
        ],
        "faq": [
            {"q": "开户法人必须到场吗？", "a": "四大行必须到场；招行/平安可上门核实（客户经理到公司，法人视频面签）；网商/微众全程在线。"},
        ],
    },
}

# ── 代理记账 ──

CAPABILITIES_ACCOUNTING = {
    "status_machine": {
        "states": [
            {"id": "new_client", "name": "新客户", "description": "新签约客户"},
            {"id": "handover_old_data", "name": "旧账交接", "description": "接手上家代账或自记账数据"},
            {"id": "initial_setup", "name": "初始化配置", "description": "账套初始化、科目设置"},
            {"id": "monthly_billing", "name": "日常做账", "description": "每月票据整理+做账"},
            {"id": "tax_filing", "name": "纳税申报", "description": "各税种按期申报"},
            {"id": "annual_settlement", "name": "年度汇算清缴", "description": "企业所得税汇算清缴"},
            {"id": "completed", "name": "已完成", "description": "本周期完成"},
        ],
        "transitions": [
            ["new_client", "handover_old_data"], ["handover_old_data", "initial_setup"],
            ["initial_setup", "monthly_billing"], ["monthly_billing", "tax_filing"],
            ["tax_filing", "monthly_billing"], ["tax_filing", "annual_settlement"],
            ["annual_settlement", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "ocr_receipt", "name": "票据OCR识别", "description": "自动识别发票/票据信息"},
        {"id": "auto_ledger", "name": "自动记账", "description": "根据票据自动生成凭证"},
        {"id": "tax_calc", "name": "税费自动计算", "description": "自动计算各税种应纳税额"},
        {"id": "tax_filing_auto", "name": "自动申报", "description": "自动提交纳税申报表"},
        {"id": "deadline_reminder", "name": "申报提醒", "description": "各税种申报截止日提醒"},
        {"id": "financial_report", "name": "报表生成", "description": "自动生成财务报表"},
    ],
    "human_required": [
        {"id": "receipt_collection", "name": "票据收集", "description": "每月收集客户票据"},
        {"id": "account_review", "name": "账务复核", "description": "会计复核AI生成的凭证"},
        {"id": "tax_filing_confirm", "name": "申报确认", "description": "确认无误后提交申报"},
    ],
    "escalation_conditions": [
        {"condition": "complex_tax", "description": "复杂的税收筹划需求"},
        {"condition": "tax_audit", "description": "税务稽查/自查"},
        {"condition": "loss_carryover", "description": "亏损弥补等特殊情况"},
    ],
    "knowledge_base": {
        "faq": [
            {"q": "代理记账多少钱？", "a": "小规模99元/月，一般纳税人199元/月。市场价200-500元/月。"},
        ],
    },
}

# ── 高企认定 ──

CAPABILITIES_HIGH_TECH = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收高企认定需求"},
            {"id": "score_evaluation", "name": "评分预评估", "description": "AI预评估企业是否符合条件"},
            {"id": "gap_analysis", "name": "差距分析", "description": "确定需要补充的材料和条件"},
            {"id": "ip_preparation", "name": "知识产权准备", "description": "补充申请知识产权"},
            {"id": "rd_expense_sorting", "name": "研发费用归集", "description": "归集近三年研发费用"},
            {"id": "materials_preparing", "name": "申报材料准备", "description": "撰写申报材料"},
            {"id": "submitted", "name": "已提交", "description": "已提交至认定机构"},
            {"id": "expert_review", "name": "专家评审", "description": "专家评审中"},
            {"id": "supplement", "name": "补充材料", "description": "需补充说明材料"},
            {"id": "approved", "name": "已认定", "description": "高新技术企业已认定"},
            {"id": "certificate_issued", "name": "证书发放", "description": "高企证书已发放"},
            {"id": "completed", "name": "已完成", "description": "全部完成"},
        ],
        "transitions": [
            ["draft", "score_evaluation"], ["score_evaluation", "gap_analysis"],
            ["gap_analysis", "ip_preparation"], ["ip_preparation", "rd_expense_sorting"],
            ["rd_expense_sorting", "materials_preparing"], ["materials_preparing", "submitted"],
            ["submitted", "expert_review"], ["expert_review", "supplement"],
            ["supplement", "expert_review"], ["expert_review", "approved"],
            ["approved", "certificate_issued"], ["certificate_issued", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "score_prediction", "name": "评分预测", "description": "AI根据企业数据预测评分"},
        {"id": "gap_report", "name": "差距报告", "description": "自动生成差距分析报告"},
        {"id": "document_template_gen", "name": "文档模板", "description": "生成申报材料模板"},
        {"id": "ip_recommendation", "name": "知识产权建议", "description": "推荐申请的知识产权类型"},
        {"id": "timeline_calc", "name": "时限预估", "description": "预估全流程时间"},
        {"id": "progress_tracking", "name": "进度跟踪", "description": "跟踪认定进度"},
        {"id": "renewal_reminder", "name": "续期提醒", "description": "高企到期前提醒续期"},
    ],
    "human_required": [
        {"id": "expert_review_coordination", "name": "专家评审协调", "description": "配合专家评审"},
        {"id": "supplement_response", "name": "补充材料准备", "description": "准备补充材料"},
        {"id": "on_site_inspection", "name": "现场考察", "description": "配合现场考察"},
    ],
    "escalation_conditions": [
        {"condition": "score_below_70", "description": "预评分低于70分"},
        {"condition": "insufficient_ip", "description": "知识产权不达标"},
        {"condition": "rd_ratio_low", "description": "研发费用占比不足"},
    ],
    "knowledge_base": {
        "scoring_criteria": [
            {"item": "知识产权", "score": "≤30分"},
            {"item": "科技成果转化能力", "score": "≤30分"},
            {"item": "研究开发组织管理水平", "score": "≤20分"},
            {"item": "企业成长性", "score": "≤20分"},
        ],
        "faq": [
            {"q": "高企认定有什么好处？", "a": "企业所得税从25%减按15%征收，直接减税40%。还有一次性补贴10-50万（各地不同）。"},
            {"q": "评分需要多少分？", "a": "总分100分，70分以上合格。核心是知识产权和成果转化，这两项占60分。"},
        ],
    },
}

# ── 专利/软著 (IP) ──

CAPABILITIES_IP = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收IP申请需求"},
            {"id": "prior_art_search", "name": "查新检索", "description": "查新检索中"},
            {"id": "document_preparing", "name": "文件撰写", "description": "撰写申请文件"},
            {"id": "document_review", "name": "文件确认", "description": "申请人与代理人确认"},
            {"id": "submitted", "name": "已提交", "description": "已提交至专利局/版权中心"},
            {"id": "formal_examination", "name": "受理", "description": "形式审查中"},
            {"id": "substantive_examination", "name": "实审", "description": "实质审查中（发明专利）"},
            {"id": "office_action", "name": "审查意见", "description": "收到审查意见通知书"},
            {"id": "reply_preparing", "name": "意见答复", "description": "准备审查意见答复"},
            {"id": "granted", "name": "授权", "description": "已授权"},
            {"id": "certificate_issued", "name": "证书发放", "description": "证书已发放"},
            {"id": "completed", "name": "已完成", "description": "全部完成"},
        ],
        "transitions": [
            ["draft", "prior_art_search"], ["prior_art_search", "document_preparing"],
            ["document_preparing", "document_review"], ["document_review", "submitted"],
            ["submitted", "formal_examination"],
            ["formal_examination", "substantive_examination"],
            ["substantive_examination", "office_action"],
            ["office_action", "reply_preparing"], ["reply_preparing", "substantive_examination"],
            ["substantive_examination", "granted"], ["granted", "certificate_issued"],
            ["certificate_issued", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "prior_art_search", "name": "查新检索", "description": "AI进行在先专利/文献检索"},
        {"id": "document_template_gen", "name": "文件模板生成", "description": "生成申请文件模板"},
        {"id": "timeline_calc", "name": "时限预估", "description": "预估审查周期"},
        {"id": "fee_calc", "name": "费用明细", "description": "计算官费+代理费"},
        {"id": "deadline_reminder", "name": "期限提醒", "description": "提醒答复期限/缴费期限"},
        {"id": "status_notification", "name": "状态通知", "description": "实时推送审查状态"},
    ],
    "human_required": [
        {"id": "patent_drafting", "name": "专利撰写", "description": "专利代理人撰写申请文件"},
        {"id": "office_action_reply", "name": "审查意见答复", "description": "撰写审查意见答复"},
        {"id": "submission", "name": "系统提交", "description": "通过CPC系统提交"},
        {"id": "certificate_collection", "name": "证书领取", "description": "领取专利/软著证书"},
    ],
    "escalation_conditions": [
        {"condition": "prior_art_found", "description": "查新发现近似在先专利"},
        {"condition": "office_action_repeated", "description": "多次审查意见通知"},
        {"condition": "rejection_expected", "description": "预期驳回需复审"},
    ],
    "knowledge_base": {
        "comparison": [
            {"type": "发明", "term": "20年", "avg_time": "18-36个月", "cost": "4500-8000"},
            {"type": "实用新型", "term": "10年", "avg_time": "6-12个月", "cost": "2500-4000"},
            {"type": "外观设计", "term": "15年", "avg_time": "4-8个月", "cost": "1500-2500"},
            {"type": "软著", "term": "50年", "avg_time": "30-60工作日", "cost": "800-1500"},
        ],
        "faq": [
            {"q": "发明和实用新型能同时申请吗？", "a": "可以，同一天就同一技术方案可以同时申请发明和实用新型。"},
        ],
    },
}

# ── 进出口备案 ──

CAPABILITIES_IE = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收进出口备案需求"},
            {"id": "materials_preparing", "name": "材料准备", "description": "备案材料准备中"},
            {"id": "foreign_trade_filing", "name": "外贸备案", "description": "对外贸易经营者备案"},
            {"id": "customs_registration", "name": "海关注册", "description": "海关报关单位注册登记"},
            {"id": "ic_card_processing", "name": "电子口岸卡", "description": "电子口岸IC卡办理中"},
            {"id": "foreign_exchange_filing", "name": "外管局备案", "description": "外汇管理局名录登记"},
            {"id": "tax_refund_filing", "name": "退税备案", "description": "出口退税备案（如需要）"},
            {"id": "completed", "name": "已完成", "description": "全部完成"},
        ],
        "transitions": [
            ["draft", "materials_preparing"], ["materials_preparing", "foreign_trade_filing"],
            ["foreign_trade_filing", "customs_registration"],
            ["customs_registration", "ic_card_processing"],
            ["ic_card_processing", "foreign_exchange_filing"],
            ["foreign_exchange_filing", "tax_refund_filing"],
            ["tax_refund_filing", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "document_checklist_gen", "name": "材料清单", "description": "生成全流程材料清单"},
        {"id": "form_auto_fill", "name": "自动填表", "description": "AI自动填写各备案表单"},
        {"id": "procedure_guide", "name": "流程指引", "description": "分步指导各环节"},
        {"id": "timeline_calc", "name": "时限预估", "description": "预估办理时限"},
        {"id": "progress_tracking", "name": "进度跟踪", "description": "跟踪各环节进度"},
    ],
    "human_required": [
        {"id": "online_submission", "name": "系统提交", "description": "在商务/海关/外管系统提交"},
        {"id": "ic_card_pickup", "name": "IC卡领取", "description": "到电子口岸窗口领取IC卡"},
        {"id": "document_mailing", "name": "文件寄送", "description": "寄送纸质材料"},
    ],
    "escalation_conditions": [
        {"condition": "special_controlled_goods", "description": "涉及管制/敏感物项"},
        {"condition": "incomplete_scope", "description": "经营范围未包含进出口相关"},
        {"condition": "urgent_deadline", "description": "急需通关"},
    ],
    "knowledge_base": {
        "faq": [
            {"q": "进出口备案需要多长时间？", "a": "全套流程约7-15个工作日。包括外贸备案（3天）、海关注册（3天）、IC卡（5天）、外管局（3天）。"},
        ],
    },
}

# ── 法律咨询 ──

CAPABILITIES_LEGAL = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收法律咨询需求"},
            {"id": "ai_analysis", "name": "AI初步分析", "description": "AI进行初步法律分析"},
            {"id": "lawyer_assigned", "name": "律师指派", "description": "分配对口专业律师"},
            {"id": "lawyer_review", "name": "律师审查", "description": "律师审阅材料和案情"},
            {"id": "consultation_delivery", "name": "咨询交付", "description": "律师出具法律意见"},
            {"id": "follow_up", "name": "后续跟进", "description": "跟进客户反馈"},
            {"id": "completed", "name": "已完成", "description": "咨询完成"},
        ],
        "transitions": [
            ["draft", "ai_analysis"], ["ai_analysis", "lawyer_assigned"],
            ["lawyer_assigned", "lawyer_review"], ["lawyer_review", "consultation_delivery"],
            ["consultation_delivery", "follow_up"], ["follow_up", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "initial_risk_analysis", "name": "初步风险分析", "description": "AI进行初步法律风险分析"},
        {"id": "lawyer_matching", "name": "律师匹配", "description": "根据案件类型匹配律师"},
        {"id": "document_checklist", "name": "材料清单", "description": "提供所需材料清单"},
        {"id": "timeline_calc", "name": "时限预估", "description": "预估处理时间"},
        {"id": "case_tracking", "name": "案件跟踪", "description": "跟踪案件进展"},
    ],
    "human_required": [
        {"id": "legal_analysis", "name": "法律分析", "description": "律师进行专业法律分析"},
        {"id": "document_review_draft", "name": "文书审查/起草", "description": "律师审查或起草法律文书"},
        {"id": "consultation_meeting", "name": "咨询会谈", "description": "律师与客户沟通"},
    ],
    "escalation_conditions": [
        {"condition": "complex_litigation", "description": "复杂诉讼/仲裁"},
        {"condition": "criminal_case", "description": "涉及刑事案件"},
        {"condition": "cross_border", "description": "跨境法律问题"},
    ],
    "knowledge_base": {
        "faq": [
            {"q": "法律咨询多少钱？", "a": "AI初筛免费，律师咨询199元起。市场价200-30000元不等。"},
        ],
    },
}

# ── 资质代办 ──

CAPABILITIES_LICENSE_APPLICATION = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收资质申请需求"},
            {"id": "requirement_analysis", "name": "需求分析", "description": "AI分析资质要求和条件"},
            {"id": "gap_assessment", "name": "差距评估", "description": "评估企业与资质要求的差距"},
            {"id": "materials_preparing", "name": "材料准备", "description": "准备申请材料"},
            {"id": "submitted", "name": "已提交", "description": "已提交至审批部门"},
            {"id": "in_review", "name": "审核中", "description": "审批部门审核中"},
            {"id": "supplement_materials", "name": "补充材料", "description": "需要补充或说明材料"},
            {"id": "on_site_inspection", "name": "现场考察", "description": "审批部门现场考察"},
            {"id": "approved", "name": "审核通过", "description": "资质申请通过"},
            {"id": "certificate_delivery", "name": "证书交付", "description": "资质证书已交付"},
            {"id": "completed", "name": "已完成", "description": "全部完成"},
        ],
        "transitions": [
            ["draft", "requirement_analysis"], ["requirement_analysis", "gap_assessment"],
            ["gap_assessment", "materials_preparing"], ["materials_preparing", "submitted"],
            ["submitted", "in_review"], ["in_review", "supplement_materials"],
            ["supplement_materials", "in_review"], ["in_review", "on_site_inspection"],
            ["on_site_inspection", "approved"], ["approved", "certificate_delivery"],
            ["certificate_delivery", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "requirement_analysis", "name": "资质条件分析", "description": "自动分析资质申请条件"},
        {"id": "eligibility_check", "name": "资格预检", "description": "检查企业是否满足基本条件"},
        {"id": "gap_report", "name": "差距报告", "description": "生成差距评估报告"},
        {"id": "material_template_gen", "name": "材料模板生成", "description": "生成申请材料模板"},
        {"id": "timeline_prediction", "name": "时限预测", "description": "预测办理时间"},
        {"id": "status_tracking", "name": "进度跟踪", "description": "跟踪审批进度"},
        {"id": "renewal_reminder", "name": "续期提醒", "description": "到期续期提醒"},
    ],
    "human_required": [
        {"id": "submission_to_agency", "name": "系统提交", "description": "在审批系统提交材料"},
        {"id": "on_site_inspection_accompany", "name": "现场考察陪同", "description": "配合现场考察"},
        {"id": "supplement_response", "name": "补充材料准备", "description": "准备补充材料"},
        {"id": "certificate_collection", "name": "证书领取", "description": "领取资质证书"},
    ],
    "escalation_conditions": [
        {"condition": "business_scope_mismatch", "description": "经营范围与资质要求不符"},
        {"condition": "capital_insufficient", "description": "注册资本/实缴不足"},
        {"condition": "staffing_gap", "description": "人员配置不达标"},
        {"condition": "site_not_qualified", "description": "办公场地不符合要求"},
        {"condition": "rejected_before", "description": "之前被驳回过"},
        {"condition": "multi_dept_approval", "description": "需要多部门联合审批"},
        {"condition": "bad_credit", "description": "企业有不良信用记录"},
    ],
    "knowledge_base": {
        "common_licenses": [
            {"type": "ICP许可证", "condition": "注册资本100万+", "time": "60-90天"},
            {"type": "食品经营许可证", "condition": "实际经营场所", "time": "20-30天"},
            {"type": "医疗器械经营备案", "condition": "专业人员+场所", "time": "20-30天"},
            {"type": "劳务派遣许可证", "condition": "注册资本200万+实缴", "time": "30-60天"},
        ],
        "faq": [
            {"q": "资质代办多少钱？", "a": "根据资质类型不同，599元起。市场价1000-5000元。"},
        ],
    },
}

# ── 商标注册 ──

CAPABILITIES_TRADEMARK = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收商标注册需求"},
            {"id": "search_in_progress", "name": "查新检索", "description": "AI进行商标查新检索"},
            {"id": "search_completed", "name": "查新完成", "description": "查新报告已出"},
            {"id": "class_recommended", "name": "分类推荐", "description": "AI推荐尼斯分类方案"},
            {"id": "materials_preparing", "name": "材料准备", "description": "准备申请材料"},
            {"id": "submitted", "name": "已提交", "description": "已提交至国家知识产权局"},
            {"id": "formal_examination", "name": "形式审查", "description": "形式审查中"},
            {"id": "substantive_examination", "name": "实质审查", "description": "实质审查中"},
            {"id": "publication", "name": "初审公告", "description": "初审公告（3个月异议期）"},
            {"id": "opposition_monitoring", "name": "异议监控", "description": "异议期监控中"},
            {"id": "registration_certificate", "name": "注册公告", "description": "核准注册，等待证书"},
            {"id": "completed", "name": "已完成", "description": "商标注册完成"},
        ],
        "transitions": [
            ["draft", "search_in_progress"], ["search_in_progress", "search_completed"],
            ["search_completed", "class_recommended"], ["class_recommended", "materials_preparing"],
            ["materials_preparing", "submitted"], ["submitted", "formal_examination"],
            ["formal_examination", "substantive_examination"],
            ["substantive_examination", "publication"],
            ["publication", "opposition_monitoring"],
            ["opposition_monitoring", "registration_certificate"],
            ["registration_certificate", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "prior_art_search", "name": "商标查新", "description": "AI进行近似商标检索分析"},
        {"id": "nice_class_recommendation", "name": "尼斯分类推荐", "description": "根据商品/服务推荐最优分类"},
        {"id": "risk_assessment", "name": "风险评估", "description": "评估注册成功率"},
        {"id": "document_template_gen", "name": "文书生成", "description": "生成申请书/委托书"},
        {"id": "fee_calc", "name": "费用计算", "description": "计算官费+服务费"},
        {"id": "timeline_prediction", "name": "时限预测", "description": "预测审查周期"},
        {"id": "opposition_monitoring", "name": "异议监控", "description": "监控3个月异议期"},
        {"id": "renewal_reminder", "name": "续展提醒", "description": "提前12个月提醒续展"},
    ],
    "human_required": [
        {"id": "submission_to_trademark_office", "name": "商标局提交", "description": "通过商标局系统提交"},
        {"id": "examination_followup", "name": "审查跟进", "description": "跟进审查进度"},
        {"id": "refusal_response", "name": "驳回应对", "description": "驳回复审申请"},
        {"id": "opposition_filing", "name": "异议申请/答辩", "description": "提交异议申请或答辩"},
        {"id": "certificate_receipt", "name": "证书领取", "description": "领取商标注册证书"},
    ],
    "escalation_conditions": [
        {"condition": "high_similarity_risk", "description": "查新发现高近似风险"},
        {"condition": "rejected_absolute_grounds", "description": "绝对理由驳回（缺乏显著性）"},
        {"condition": "opposition_filed", "description": "第三方提出异议"},
        {"condition": "multi_class_disputes", "description": "多类别争议"},
        {"condition": "prior_rights_conflict", "description": "在先权利冲突"},
    ],
    "knowledge_base": {
        "official_fees": [
            {"item": "商标注册申请", "fee": "270元/类（限10个项目）", "note": "超出10项每项加收30元"},
            {"item": "商标续展", "fee": "500元/类"},
            {"item": "商标转让", "fee": "450元/类"},
            {"item": "商标变更", "fee": "150元/类"},
        ],
        "faq": [
            {"q": "商标注册多少钱？", "a": "官费270元/类+服务费299元/类=569元/类起。市场价800-1500元/类。"},
            {"q": "TM和R的区别？", "a": "TM表示已申请受理中，R表示已注册受法律保护。"},
            {"q": "注册一个类够吗？", "a": "建议核心业务类必注，相关类辅注。比如做软件：第9类（软件）+第42类（技术开发）+第35类（广告）。"},
        ],
    },
}

# ── 工商变更 ──

CAPABILITIES_COMPANY_CHANGE = {
    "status_machine": {
        "states": [
            {"id": "draft", "name": "需求接收", "description": "已接收变更需求，等待AI分析"},
            {"id": "requirement_analysis", "name": "变更分析", "description": "AI分析变更事项，确定所需材料和流程"},
            {"id": "documents_preparing", "name": "材料准备", "description": "生成变更申请书、决议、章程修正案等"},
            {"id": "documents_review", "name": "内部复核", "description": "AI预检材料完整性"},
            {"id": "signing", "name": "签署文件", "description": "e签宝或线下签署"},
            {"id": "shareholder_tax", "name": "个税申报（股权变更）", "description": "股权转让溢价需先完税"},
            {"id": "reduction_notice", "name": "减资公告期", "description": "登报公告45天（减资场景）"},
            {"id": "submitted", "name": "已提交", "description": "材料已提交市监局"},
            {"id": "in_review", "name": "审核中", "description": "市监局审核中"},
            {"id": "correction", "name": "补正", "description": "需补充或修改材料"},
            {"id": "approved", "name": "审核通过", "description": "变更已核准"},
            {"id": "license_updated", "name": "执照更新", "description": "换发新执照"},
            {"id": "completed", "name": "已完成", "description": "全部完成"},
        ],
        "transitions": [
            ["draft", "requirement_analysis"], ["requirement_analysis", "documents_preparing"],
            ["documents_preparing", "documents_review"], ["documents_review", "signing"],
            ["signing", "shareholder_tax"], ["shareholder_tax", "submitted"],
            ["signing", "reduction_notice"], ["reduction_notice", "submitted"],
            ["signing", "submitted"], ["submitted", "in_review"],
            ["in_review", "correction"], ["correction", "in_review"],
            ["in_review", "approved"], ["approved", "license_updated"],
            ["license_updated", "completed"],
        ],
    },
    "agent_auto": [
        {"id": "change_analysis", "name": "变更事项分析", "description": "分析所需材料、流程和时限"},
        {"id": "document_template_gen", "name": "文书模板生成", "description": "自动生成决议/章程修正案草案"},
        {"id": "material_pre_review", "name": "材料AI预审", "description": "检查材料完整性和一致性"},
        {"id": "tax_implication_analysis", "name": "税务影响分析", "description": "股权转让个税估算、印花税计算"},
        {"id": "timeline_calc", "name": "时限预估", "description": "全流程时限预估"},
        {"id": "fee_calculation", "name": "费用计算", "description": "行政收费+服务费"},
        {"id": "progress_tracking", "name": "进度跟踪", "description": "实时跟踪审核进度"},
        {"id": "subsequent_reminder", "name": "后续事项提醒", "description": "完成后提醒税务银行资质变更"},
    ],
    "human_required": [
        {"id": "document_filing", "name": "材料提交", "description": "到窗口提交纸质材料"},
        {"id": "identity_verification", "name": "身份核验协调", "description": "协调新法人/股东扫脸认证"},
        {"id": "reduction_notice_publishing", "name": "减资公告发布", "description": "发布减资公告"},
        {"id": "correction_response", "name": "补正响应", "description": "准备补充材料"},
        {"id": "tax_declaration_guidance", "name": "个税申报指导", "description": "协助股权转让方完税"},
        {"id": "license_collection", "name": "执照领取/寄送", "description": "领取新执照"},
    ],
    "escalation_conditions": [
        {"condition": "cross_district", "description": "跨区迁移涉及两个登记机关"},
        {"condition": "capital_decrease", "description": "减资需45天公告期"},
        {"condition": "equity_transfer_with_tax", "description": "股权转让溢价需先完税"},
        {"condition": "pre_license_involved", "description": "涉及前置许可审批"},
        {"condition": "articles_major_revision", "description": "章程重大修订"},
        {"condition": "shareholder_disagreement", "description": "股东不同意变更"},
        {"condition": "foreign_investment_restriction", "description": "外资准入限制行业"},
        {"condition": "multiple_changes", "description": "同时变更多项事项"},
    ],
    "knowledge_base": {
        "legal_basis": ["《公司法》(2024修订)", "《市场主体登记管理条例》", "《实施细则》"],
        "material_matrix": {
            "company_name": ["名称变更申请书", "股东会决议", "章程修正案", "原执照"],
            "address": ["住所变更申请书", "股东会决议", "章程修正案", "新地址证明", "租赁合同", "原执照"],
            "legal_representative": ["法定代表人变更申请书", "股东会决议", "免职文件", "任职文件", "新法人身份证"],
            "registered_capital": ["注册资本变更申请书", "股东会决议", "章程修正案", "验资报告", "减资公告", "原执照"],
            "business_scope": ["经营范围变更申请书", "股东会决议", "章程修正案", "前置许可", "原执照"],
            "shareholder": ["股权变更申请书", "股东会决议", "股权转让协议", "章程修正案", "新股东证件", "完税证明", "原执照"],
            "executive": ["高管变更备案申请书", "股东会决议", "任免文件", "新任职人员身份证"],
            "articles": ["章程备案申请书", "股东会决议", "修订后章程"],
            "contact_person": ["联络员变更申请表", "新联络员身份证"],
        },
        "timeline": {
            "online_submission": "1-2个工作日", "review_period": "3-5个工作日",
            "reduction_notice": "45天（公告期）", "cross_district": "7-15个工作日",
        },
        "faq": [
            {"q": "工商变更需要多少天？", "a": "一般3-7天；减资约2个月（含45天公告）；跨区迁址7-15天。"},
            {"q": "法人变更后还要办什么？", "a": "税务变更→银行信息变更→社保/公积金→资质许可证变更。"},
            {"q": "股权转让要交税吗？", "a": "溢价转让交个税（差额20%）+印花税（万分之五）。平价/低价不涉及。"},
        ],
    },
}


# ═══════════════════════════════════════════════
# 服务注册表 (SERVICE_REGISTRY)
# ═══════════════════════════════════════════════

SERVICE_REGISTRY = {
    "company_registration": {
        "name": "公司注册",
        "description": "全国有限责任公司设立。核名 -> 材料准备 -> 工商提交 -> 执照领取，全流程代办。法人无需到场，e签宝远程签名。",
        "status": "live",
        "schema_model": CompanyRegistrationParams,
        "estimated_days": "7-14",
        "price_range": "699-1299",
        "required_documents": [
            "公司备选名称（至少3个）",
            "全体股东身份证复印件",
            "股东出资比例及出资方式",
            "经营范围描述",
            "注册地址产权证明/租赁合同",
            "法定代表人、执行董事、监事任职信息",
            "全体股东实名认证（工商App）",
        ],
        "capabilities": CAPABILITIES_COMPANY_REGISTRATION,
        "workflow_steps": [
            {"step_id": "name_reservation", "name": "核名", "order": 1, "agent_auto": True},
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
        "name": "高新技术企业认定",
        "description": "国家级高新技术企业认定全流程。评分预评估 → 差距分析 → 知识产权准备 → 研发费用归集 → 申报材料撰写 → 提交 → 专家评审 → 认定。企业所得税减按15%征收。",
        "status": "live",
        "schema_model": HighTechApplicationParams,
        "estimated_days": "6-12个月",
        "price_range": "8000-30000",
        "required_documents": [
            "企业营业执照副本",
            "近三年年度审计报告",
            "近三年研发费用专项审计报告",
            "近一年高新技术产品收入专项审计报告",
            "知识产权证书（专利/软著/集成电路布图）",
            "研发人员名单及学历证明",
            "研发管理制度文件",
        ],
        "capabilities": CAPABILITIES_HIGH_TECH,
        "workflow_steps": [
            {"step_id": "score_evaluation", "name": "评分预评估", "order": 1, "agent_auto": True},
            {"step_id": "gap_analysis", "name": "差距分析", "order": 2, "agent_auto": True},
            {"step_id": "ip_preparation", "name": "知识产权准备", "order": 3, "agent_auto": False},
            {"step_id": "rd_expense_sorting", "name": "研发费用归集", "order": 4, "agent_auto": False},
            {"step_id": "material_writing", "name": "申报材料撰写", "order": 5, "agent_auto": False},
            {"step_id": "submit_and_follow", "name": "提交及跟进", "order": 6, "agent_auto": False},
            {"step_id": "expert_review", "name": "专家评审", "order": 7, "agent_auto": False},
            {"step_id": "certificate_receive", "name": "证书领取", "order": 8, "agent_auto": False},
        ],
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
        "description": "进出口权全套备案服务。对外贸易经营者备案 -> 海关注册 -> 电子口岸IC卡 -> 外汇管理局名录登记 -> 出口退税备案（可选）。一口接入，全流程代办。",
        "status": "live",
        "schema_model": ImportExportParams,
        "estimated_days": "7-15",
        "price_range": "800-2500",
        "required_documents": [
            "营业执照副本",
            "公司章程",
            "公司中英文名称及英文地址",
            "法定代表人身份证",
            "海关业务联系人身份证",
            "公司电话及邮箱",
            "主要进出口产品类别说明",
        ],
        "capabilities": CAPABILITIES_IE,
        "workflow_steps": [
            {"step_id": "materials_check", "name": "材料核验", "order": 1, "agent_auto": True},
            {"step_id": "foreign_trade_filing", "name": "外贸经营者备案", "order": 2, "agent_auto": False},
            {"step_id": "customs_registration", "name": "海关注册登记", "order": 3, "agent_auto": False},
            {"step_id": "ic_card", "name": "电子口岸IC卡", "order": 4, "agent_auto": False},
            {"step_id": "foreign_exchange", "name": "外管局名录登记", "order": 5, "agent_auto": False},
            {"step_id": "tax_refund_filing", "name": "出口退税备案", "order": 6, "agent_auto": False, "optional": True},
        ],
    },
    "legal_consulting": {
        "name": "法律咨询",
        "description": "AI初筛+专业律师终审。合同审查、协议起草、纠纷咨询、劳动人事、知识产权、合规、投融资等。AI免费初筛后匹配对口专业律师。",
        "status": "live",
        "schema_model": LegalConsultingParams,
        "estimated_days": "1-3（AI初筛即时出结果，律师意见1-3个工作日）",
        "price_range": "200-30000",
        "required_documents": [
            "问题/案情详细描述",
            "相关合同/协议（如有）",
            "对方当事人信息（如有）",
            "已有法律文书（如有）",
        ],
        "capabilities": CAPABILITIES_LEGAL,
        "workflow_steps": [
            {"step_id": "ai_initial_analysis", "name": "AI初筛", "order": 1, "agent_auto": True},
            {"step_id": "lawyer_matching", "name": "律师匹配", "order": 2, "agent_auto": True},
            {"step_id": "lawyer_consultation", "name": "律师咨询", "order": 3, "agent_auto": False},
            {"step_id": "delivery", "name": "交付意见", "order": 4, "agent_auto": False},
        ],
    },
    "accounting": {
        "name": "代理记账",
        "description": "智能代理记账服务。票据OCR识别→AI自动做账→人工复核→智能申报。小规模99元/月，一般纳税人199元/月。全流程透明可追溯。",
        "status": "live",
        "schema_model": AccountingParams,
        "estimated_days": "持续服务（按月）",
        "price_range": "99/月",
        "required_documents": [
            "营业执照副本",
            "银行开户许可证",
            "税务登记证（或已完成税务登记）",
            "法人/财务负责人身份证",
            "上一期财务报表（如有）",
            "税控盘/UKey信息",
            "每月票据/发票",
        ],
        "capabilities": CAPABILITIES_ACCOUNTING,
        "workflow_steps": [
            {"step_id": "contract_signing", "name": "签约", "order": 1, "agent_auto": True},
            {"step_id": "data_handover", "name": "数据交接", "order": 2, "agent_auto": True},
            {"step_id": "initial_setup", "name": "账套初始化", "order": 3, "agent_auto": False},
            {"step_id": "monthly_receipt_collection", "name": "每月收集票据", "order": 4, "agent_auto": False},
            {"step_id": "ocr_and_ledger", "name": "OCR+AI做账", "order": 5, "agent_auto": True},
            {"step_id": "manual_review", "name": "人工复核", "order": 6, "agent_auto": False},
            {"step_id": "tax_filing", "name": "纳税申报", "order": 7, "agent_auto": True},
            {"step_id": "report_delivery", "name": "报表交付", "order": 8, "agent_auto": True},
        ],
    },
    "tax_registration": {
        "name": "税务登记",
        "description": "企业税务登记全流程代办。税种核定 -> 纳税人类型选择（小规模/一般纳税人） -> 发票申领 -> 税务UKey申请 -> 三方扣税协议签订。AI智能推荐最优纳税人类型。",
        "status": "live",
        "schema_model": TaxRegistrationParams,
        "estimated_days": "5-10",
        "price_range": "199",
        "required_documents": [
            "营业执照正副本原件",
            "公章",
            "法定代表人身份证原件",
            "财务负责人身份证原件",
            "办税人身份证原件",
            "银行开户许可证/基本户信息",
            "经营地址证明材料",
            "公司章程复印件",
        ],
        "capabilities": CAPABILITIES_TAX_REGISTRATION,
        "workflow_steps": [
            {"step_id": "form_prefill", "name": "自动预填表单", "order": 1, "agent_auto": True},
            {"step_id": "taxpayer_analysis", "name": "纳税人类型推荐", "order": 2, "agent_auto": True},
            {"step_id": "document_preparation", "name": "材料准备", "order": 3, "agent_auto": True},
            {"step_id": "bureau_submit", "name": "税务局提交", "order": 4, "agent_auto": False},
            {"step_id": "tax_type_assessment", "name": "税种核定", "order": 5, "agent_auto": False},
            {"step_id": "invoice_quota", "name": "发票限额核定", "order": 6, "agent_auto": False},
            {"step_id": "ukey_pickup", "name": "UKey领取", "order": 7, "agent_auto": False},
            {"step_id": "agreement_signing", "name": "三方扣税协议", "order": 8, "agent_auto": True},
        ],
    },
    "bank_account": {
        "name": "银行开户",
        "description": "企业银行开户全流程代办。AI智能推荐银行 -> 预约 -> 材料准备 -> 上门核实 -> 账户激活。法人无需到场可选招行/平安上门核实或网商/微众全程在线。",
        "status": "live",
        "schema_model": BankAccountParams,
        "estimated_days": "5-10",
        "price_range": "299",
        "required_documents": [
            "营业执照正副本原件",
            "公章、财务章、法人章",
            "法定代表人身份证原件",
            "公司章程",
            "经营场地证明材料（租赁合同/产权证）",
            "股东会决议（开户）",
            "预留印鉴卡（银行提供）",
            "网银管理员身份证（如需）",
        ],
        "capabilities": CAPABILITIES_BANK_ACCOUNT,
        "workflow_steps": [
            {"step_id": "bank_recommendation", "name": "AI智能推荐银行", "order": 1, "agent_auto": True},
            {"step_id": "appointment", "name": "预约办理", "order": 2, "agent_auto": True},
            {"step_id": "document_preparation", "name": "材料准备", "order": 3, "agent_auto": True},
            {"step_id": "on_site_visit", "name": "上门核实/现场办理", "order": 4, "agent_auto": False},
            {"step_id": "account_activation", "name": "账户激活", "order": 5, "agent_auto": False},
            {"step_id": "online_banking", "name": "网银开通", "order": 6, "agent_auto": False},
        ],
    },
    "license_application": {
        "name": "资质代办",
        "description": "企业资质许可证代办。ICP许可证、食品经营许可证、医疗器械经营备案、文网文、出版物、卫生许可、道路运输、劳务派遣、人力资源服务、危化品许可、广播电视制作等12+类资质。全流程代办。",
        "status": "live",
        "schema_model": LicenseApplicationParams,
        "estimated_days": "视资质类型而定（20-90天）",
        "price_range": "599",
        "required_documents": [
            "营业执照正副本",
            "法定代表人身份证",
            "公司章程",
            "经营场所证明（租赁合同/产权证）",
            "专业人员资质证明（视资质类型）",
            "验资报告（如需）",
            "行业主管部门前置审批文件（如有）",
        ],
        "capabilities": CAPABILITIES_LICENSE_APPLICATION,
        "workflow_steps": [
            {"step_id": "requirement_analysis", "name": "资质条件分析", "order": 1, "agent_auto": True},
            {"step_id": "gap_assessment", "name": "差距评估", "order": 2, "agent_auto": True},
            {"step_id": "material_preparation", "name": "材料准备", "order": 3, "agent_auto": False},
            {"step_id": "submission", "name": "提交审批", "order": 4, "agent_auto": False},
            {"step_id": "review", "name": "审批跟进", "order": 5, "agent_auto": False},
            {"step_id": "certificate_delivery", "name": "证书交付", "order": 6, "agent_auto": False},
        ],
    },
    "trademark": {
        "name": "商标注册",
        "description": "商标注册全流程。查新检索 -> 尼斯分类推荐 -> 申请材料准备 -> 商标局提交 -> 审查跟进 -> 异议应对 -> 领证。支持新申请/续展/转让/变更/异议。覆盖45个国际分类。",
        "status": "live",
        "schema_model": TrademarkParams,
        "estimated_days": "6-12个月（新申请）",
        "price_range": "299/类",
        "required_documents": [
            "商标图样（800x800以上JPG/PDF）",
            "营业执照副本扫描件",
            "法人/申请人身份证扫描件",
            "商标注册申请书（系统生成）",
            "商标代理委托书（系统生成）",
            "优先权证明文件（如有）",
        ],
        "capabilities": CAPABILITIES_TRADEMARK,
        "workflow_steps": [
            {"step_id": "search", "name": "商标查新", "order": 1, "agent_auto": True},
            {"step_id": "class_recommendation", "name": "分类推荐", "order": 2, "agent_auto": True},
            {"step_id": "document_preparation", "name": "材料生成", "order": 3, "agent_auto": True},
            {"step_id": "submission", "name": "商标局提交", "order": 4, "agent_auto": False},
            {"step_id": "examination", "name": "审查跟进", "order": 5, "agent_auto": False},
            {"step_id": "objection_handling", "name": "异议应对", "order": 6, "agent_auto": False},
            {"step_id": "certificate_receipt", "name": "领证", "order": 7, "agent_auto": False},
        ],
    },
    "company_change": {
        "name": "工商变更",
        "description": "工商登记变更全流程。法人变更、股东变更、经营范围变更、注册资本变更（含增/减资）、地址变更（含跨区迁址）、名称变更、高管变更、章程备案、联络人员变更。AI自动生成决议和章程修正案，e签宝远程签署。",
        "status": "live",
        "schema_model": CompanyChangeParams,
        "estimated_days": "3-7（一般变更）/ ~60（减资含公告期）/ 7-15（跨区迁址）",
        "price_range": "399",
        "required_documents": [
            "营业执照正副本原件",
            "公章",
            "原法定代表人身份证（法人变更）",
            "新法定代表人身份证及手机号（法人变更）",
            "股东会决议（系统生成）",
            "章程修正案（系统生成）",
            "股权转让协议（股权变更）",
            "新地址产权证明/租赁合同（地址变更）",
            "新股东身份证/执照（股东变更）",
            "减资公告证明（减资场景）",
        ],
        "capabilities": CAPABILITIES_COMPANY_CHANGE,
        "workflow_steps": [
            {"step_id": "change_analysis", "name": "变更分析", "order": 1, "agent_auto": True},
            {"step_id": "document_generation", "name": "文书生成", "order": 2, "agent_auto": True},
            {"step_id": "document_review", "name": "内部复核", "order": 3, "agent_auto": True},
            {"step_id": "signing", "name": "签署文件", "order": 4, "agent_auto": False},
            {"step_id": "submission", "name": "工商提交", "order": 5, "agent_auto": False},
            {"step_id": "review", "name": "市监局审核", "order": 6, "agent_auto": False},
            {"step_id": "license_update", "name": "换发执照", "order": 7, "agent_auto": False},
        ],
    },
    "team_building": {
        "name": "团建策划",
        "description": "企业团队建设活动策划与执行。户外拓展、室内团建、主题工作坊等。AI根据团队人数、预算、偏好推荐最优方案。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "3-7",
        "price_range": "按方案报价",
        "capabilities": None,
    },
    "business_dining": {
        "name": "商务宴请",
        "description": "商务宴请一站式安排。餐厅推荐、菜单定制、包间预订、酒水搭配。AI根据接待规格、预算、口味偏好推荐。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "1-3",
        "price_range": "免费咨询",
        "capabilities": None,
    },
    "corporate_procurement": {
        "name": "企业采购",
        "description": "企业办公用品、设备、礼品等采购。比价后报价，透明中间价。AI根据需求自动比价推荐最优供应商。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "2-5",
        "price_range": "按需报价",
        "capabilities": None,
    },
    "logistics_delivery": {
        "name": "物流配送",
        "description": "企业物流配送服务。文件、包裹、货物等。对接多家运力，选最优方案。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "1-3",
        "price_range": "比价报价",
        "capabilities": None,
    },
    "sales_outsourcing": {
        "name": "销售外包",
        "description": "企业销售业务外包服务。电销、地推、渠道拓展等。按效果付费，免费需求匹配。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "视项目而定",
        "price_range": "按效果付费",
        "capabilities": None,
    },
    "third_party_operations": {
        "name": "代运营",
        "description": "企业新媒体/电商平台代运营。抖音、小红书、淘宝、京东等。免费方案推荐。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "月度服务",
        "price_range": "3000-20000/月",
        "capabilities": None,
    },
    "recruitment_outsourcing": {
        "name": "猎头/招聘外包",
        "description": "企业招聘外包服务。高端猎头、批量招聘、RPO。按结果收费。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "视职位而定",
        "price_range": "年薪15-25%",
        "capabilities": None,
    },
    "corporate_training": {
        "name": "企业培训",
        "description": "企业内训服务。管理培训、技能培训、团建培训等。免费比价，推荐最优讲师。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "按场次",
        "price_range": "5000-50000/场",
        "capabilities": None,
    },
    "manufacturing_sampling": {
        "name": "代工打样",
        "description": "工厂代工/打样/小批量生产。免费工厂匹配，按量报价。覆盖电子、服装、五金、塑料等行业。",
        "status": "planning",
        "schema_model": None,
        "estimated_days": "视产品而定",
        "price_range": "按量报价",
        "capabilities": None,
    },
}

VALID_TASK_TYPES = list(SERVICE_REGISTRY.keys())

# ═══════════════════════════════════════════════
# 超值定价 (v0.5.0, credits计价, 1 credit ≈ 1 RMB)
# ═══════════════════════════════════════════════

SERVICE_PRICING = {
    "company_registration": {"base_price": 499, "market_price": "699-1299", "cheap_reason": "流程标准化，AI预填+人工跑腿，比代记账公司便宜30%"},
    "high_tech_application": {"base_price": 5000, "market_price": "8000-30000", "cheap_reason": "评分预评估AI化，减少无效申报"},
    "ip_application": {"base_price": 599, "market_price": "800-8000", "cheap_reason": "查新和撰写AI辅助，降低人工成本"},
    "trademark": {"base_price": 299, "market_price": "800-1500/类", "cheap_reason": "AI查新+模板化，每类收费比市场省80%"},
    "import_export": {"base_price": 599, "market_price": "800-2500", "cheap_reason": "材料预审AI化，一次性通过率提升"},
    "legal_consulting": {"base_price": 199, "market_price": "200-30000", "cheap_reason": "AI初筛+律师终审，降低咨询门槛"},
    "accounting": {"base_price": 99, "market_price": "200/月", "cheap_reason": "票据OCR+AI记账，人工复核更低成本"},
    "tax_registration": {"base_price": 199, "market_price": "300-500", "cheap_reason": "AI预填+人工跑腿"},
    "bank_account": {"base_price": 299, "market_price": "300-800", "cheap_reason": "资料预审AI化，一次通过"},
    "license_application": {"base_price": 599, "market_price": "1000-5000", "cheap_reason": "材料AI预审，减少返工"},
    "company_change": {"base_price": 399, "market_price": "500-2000", "cheap_reason": "流程AI化，效率翻倍"},
    "team_building": {"base_price": 0, "market_price": "按方案报价", "cheap_reason": "免费咨询方案，按需求报价"},
    "business_dining": {"base_price": 0, "market_price": "免费咨询", "cheap_reason": "免费推荐，按消费结算"},
    "corporate_procurement": {"base_price": 0, "market_price": "按需报价", "cheap_reason": "比价后报价，透明中间价"},
    "logistics_delivery": {"base_price": 0, "market_price": "比价报价", "cheap_reason": "对接多家运力，选最优"},
    "sales_outsourcing": {"base_price": 0, "market_price": "按效果付费", "cheap_reason": "免费需求匹配，谈成收费"},
    "third_party_operations": {"base_price": 0, "market_price": "3000-20000/月", "cheap_reason": "免费方案推荐"},
    "recruitment_outsourcing": {"base_price": 0, "market_price": "年薪15-25%", "cheap_reason": "按结果收费"},
    "corporate_training": {"base_price": 0, "market_price": "5000-50000/场", "cheap_reason": "免费比价，推荐最优讲师"},
    "manufacturing_sampling": {"base_price": 0, "market_price": "按量报价", "cheap_reason": "免费工厂匹配"},
}
