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
    customer_id: Optional[str] = Field(None, description="客户ID（可选，传了则自动扣款）")

class TaskUpdate(BaseModel):
    status: str = Field(..., description="pending | in_progress | completed | failed")
    result: Optional[Dict[str, Any]] = None
    note: Optional[str] = Field(None, description="状态变更备注")

class TaskResponse(BaseModel):
    task_id: str
    type: str
    status: str
    params: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None
    customer_id: Optional[str] = None
    price: float = 0
    created_at: str
    updated_at: str

class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

class TaskNoteCreate(BaseModel):
    note: str = Field(..., description="任务备注内容")

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
# 缺失模型集合 (Added from router analysis)
# ═══════════════════════════════════════════════


class TaskLogEntry(BaseModel):
    action: str
    note: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    created_at: str


def get_valid_transitions(current_status: str) -> list:
    """返回当前状态允许的下一个状态列表"""
    transitions = {
        "draft": ["processing", "failed"],
        "processing": ["completed", "failed", "draft"],
        "completed": [],
        "failed": ["draft"],
    }
    return transitions.get(current_status, [])


class DashboardResponse(BaseModel):
    task_counts: Dict[str, int]
    total_tasks: int
    supplier_counts: Dict[str, int]
    total_suppliers: int
    customer_counts: Dict[str, int]
    total_customers: int
    total_credits_in_system: int


class ServiceInfo(BaseModel):
    type: str
    name: str
    description: str
    status: str
    json_schema: Optional[Dict[str, Any]] = None
    estimated_days: Optional[str] = None
    price_range: Optional[str] = None
    required_documents: Optional[List[str]] = None
    capabilities: Optional[Dict[str, Any]] = None


class ServiceListResponse(BaseModel):
    services: List[ServiceInfo]


def _get_json_schema(model_class) -> Optional[Dict[str, Any]]:
    """Generate JSON schema from a Pydantic model class."""
    if model_class is None:
        return None
    try:
        return model_class.model_json_schema()
    except Exception:
        return None


def _inject_validation_rules(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Inject additional validation rules into schema."""
    if not schema or not isinstance(schema, dict):
        return schema or {}
    properties = schema.get("properties", {})
    for field_name, field_schema in properties.items():
        if isinstance(field_schema, dict):
            if field_schema.get("minLength"):
                field_schema["min_length"] = field_schema["minLength"]
            if field_schema.get("maxLength"):
                field_schema["max_length"] = field_schema["maxLength"]
    return schema


class StepProgress(BaseModel):
    step_id: str
    name: str
    status: str
    pct: int
    blocker: Optional[str] = None


class TaskProgressResponse(BaseModel):
    task_id: str
    current_state: str
    overall_progress_pct: int
    estimated_remaining_days: int
    step_progress: List[StepProgress]


class DocumentInfo(BaseModel):
    doc_type: str
    doc_name: str
    doc_status: str
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
    doc_types: Optional[List[str]] = Field(None, description="要生成的文书类型列表，不传则生成全部")


class DocumentGenerateResponse(BaseModel):
    task_id: str
    documents: List[DocumentInfo]


VALID_SUPPLIER_STATUSES = ["pending", "approved", "rejected"]


class SupplierCreate(BaseModel):
    name: str = Field(..., description="供应商名称")
    phone: str = Field(..., description="联系电话")
    wechat: str = Field(..., description="微信号")
    city: str = Field(..., description="所在城市")
    service_types: List[str] = Field(..., description="服务品类ID列表")
    regions: List[str] = Field(default_factory=list, description="覆盖区域列表")
    specialties: List[str] = Field(default_factory=list, description="专长列表")
    id_number: str = Field(..., description="身份证号")
    qualification_desc: str = Field(..., description="资质描述")


class SupplierUpdate(BaseModel):
    status: str = Field(..., description="审核状态: pending / approved / rejected")
    notes: Optional[str] = Field(None, description="审核备注")


class SupplierInfoUpdate(BaseModel):
    regions: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    rating: Optional[float] = Field(None, ge=0, le=5, description="评分 (0-5)")
    verified: Optional[bool] = None
    available: Optional[bool] = None
    notes: Optional[str] = None


class SupplierInfo(BaseModel):
    id: int
    name: str
    phone: str
    wechat: str
    city: str
    service_types: List[str]
    regions: List[str]
    specialties: List[str]
    id_number: str
    qualification_desc: str
    status: str
    rating: float = 0
    completed_tasks: int = 0
    verified: bool = False
    available: bool = True
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class SupplierListResponse(BaseModel):
    suppliers: List[SupplierInfo]
    total: int


class CustomerCreate(BaseModel):
    name: str = Field(..., description="客户名称")
    email: str = Field(..., description="邮箱")
    phone: str = Field(..., description="手机号")
    company_name: str = Field(..., description="公司名称")
    initial_credits: int = Field(0, ge=0, description="初始赠送credits")
    notes: Optional[str] = Field(None, description="备注")


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CustomerInfo(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    company_name: str
    credits_balance: int = 0
    total_spent: int = 0
    total_tasks: int = 0
    status: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class CustomerListResponse(BaseModel):
    customers: List[CustomerInfo]
    total: int


class CreditRecharge(BaseModel):
    amount: int = Field(..., gt=0, description="充值金额（credits）")
    description: Optional[str] = Field(None, description="充值说明")


class CreditTransactionInfo(BaseModel):
    id: int
    customer_id: str
    task_id: Optional[str] = None
    amount: int
    balance_before: int = 0
    balance_after: int = 0
    type: str
    description: Optional[str] = None
    created_at: str


class CreditTransactionListResponse(BaseModel):
    transactions: List[CreditTransactionInfo]
    total: int


class FileInfo(BaseModel):
    file_id: int
    file_name: str
    file_type: str
    file_size: int
    uploaded_at: str


# ═══════════════════════════════════════════════
# 板块一·十二：团建策划 (team_building)
# ═══════════════════════════════════════════════

class TeamBuildingParams(BaseModel):
    # ── 企业基本信息 ──
    company_name: str = Field(..., description="企业名称")
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")

    # ── 团队信息 ──
    team_size: int = Field(..., ge=1, description="参与人数")
    team_composition: Optional[str] = Field(None, description="团队构成: all_staff（全员）/ department（部门）/ cross_dept（跨部门）/ new_employees（新员工）/ executives（管理层）")
    age_distribution: Optional[str] = Field(None, description="年龄分布: young（偏年轻）/ mixed（混合）/ senior（偏资深）/ unknown（不确定）")

    # ── 活动偏好 ──
    activity_types: List[str] = Field(..., min_length=1, description="活动类型偏好: outdoor（户外拓展）/ indoor（室内团建）/ sports（体育运动）/ workshop（主题工作坊）/ games（竞技游戏）/ travel（出游旅行）/ creative（创意手工）/ charity（公益）/ escape_room（密室逃脱）/ board_games（桌游）/ other（其他）")
    activity_intensity: str = Field("moderate", description="活动强度: light（轻松）/ moderate（适中）/ intense（高强度）")
    theme_preferences: Optional[List[str]] = Field(None, description="主题偏好: team_bonding（团队融合）/ competitive（竞技对抗）/ creative（创意创新）/ relaxation（休闲放松）/ culture（企业文化）")

    # ── 预算 ──
    budget_per_person: float = Field(..., ge=0, description="人均预算（元）")
    total_budget_ceiling: Optional[float] = Field(None, ge=0, description="总预算上限（元）")
    budget_includes: Optional[List[str]] = Field(None, description="预算包含项目: activity（活动费）/ meals（餐饮）/ transport（交通）/ accommodation（住宿）/ materials（物料）/ photography（摄影）")

    # ── 时间安排 ──
    preferred_date: Optional[str] = Field(None, description="首选日期（YYYY-MM-DD）")
    preferred_dates: Optional[List[str]] = Field(None, description="备选日期列表")
    preferred_time_slot: str = Field("full_day", description="时段: morning（上午）/ afternoon（下午）/ full_day（全天）/ multi_day（多日）")
    duration_days: int = Field(1, ge=1, description="活动天数")

    # ── 地点 ──
    city: str = Field(..., description="所在城市")
    preferred_area: Optional[str] = Field(None, description="首选区域")
    location_preference: str = Field("outdoor", description="场地偏好: outdoor（户外）/ indoor（室内）/ open_to_both（均可）")
    distance_preference: Optional[str] = Field(None, description="距离偏好: city_center（市区）/ suburb（近郊）/ out_of_town（远郊）/ no_limit（不限）")

    # ── 餐饮需求 ──
    has_dining: bool = Field(True, description="是否安排餐饮")
    meal_type: Optional[str] = Field(None, description="餐饮类型: buffet（自助餐）/ table（桌餐）/ bbq（烧烤）/ boxed（盒饭）/ no_meal（不安排）")
    dietary_restrictions: Optional[str] = Field(None, description="饮食禁忌/特殊要求（如清真、素食等）")

    # ── 交通住宿 ──
    has_transportation: bool = Field(False, description="是否需安排交通（大巴/包车）")
    pickup_location: Optional[str] = Field(None, description="集合地点")
    has_accommodation: bool = Field(False, description="是否需要住宿")
    accommodation_standard: Optional[str] = Field(None, description="住宿标准: economy（经济）/ business（商务）/ luxury（高档）")
    room_count: Optional[int] = Field(None, ge=1, description="房间数量")

    # ── 附加需求 ──
    has_photography: bool = Field(False, description="是否需要摄影/摄像")
    has_material_preparation: bool = Field(True, description="是否需要物料准备（横幅、队服、奖牌等）")
    custom_material_notes: Optional[str] = Field(None, description="定制物料要求")
    need_insurance: bool = Field(True, description="是否需要购买活动保险")
    special_requirements: Optional[str] = Field(None, description="特殊需求说明（如场地无障碍、过敏原等）")
    notes: Optional[str] = Field(None, description="补充说明")

    @field_validator("activity_types")
    @classmethod
    def validate_activity_types(cls, v):
        valid = {"outdoor", "indoor", "sports", "workshop", "games", "travel", "creative", "charity", "escape_room", "board_games", "other"}
        for t in v:
            if t not in valid:
                raise ValueError(f"无效的活动类型: {t}，可选: {', '.join(sorted(valid))}")
        return v

    @field_validator("team_size")
    @classmethod
    def validate_team_size(cls, v):
        if v > 500:
            raise ValueError(f"团队人数超过500人: {v}，超大团建请备注特殊需求")
        return v


# ═══════════════════════════════════════════════
# 板块一·十三：商务宴请 (business_dining)
# ═══════════════════════════════════════════════

class BusinessDiningParams(BaseModel):
    # ── 企业/联系人信息 ──
    company_name: str = Field(..., description="企业名称")
    contact_name: str = Field(..., min_length=1, description="联系人姓名")
    contact_phone: str = Field(..., min_length=11, description="联系人手机号")
    contact_email: Optional[str] = Field(None, description="联系邮箱")

    # ── 用餐信息 ──
    guest_count: int = Field(..., ge=1, description="用餐人数")
    guest_importance: str = Field("regular", description="宾客重要程度: regular（普通）/ important（重要）/ vip（核心VIP）/ government（政府）")
    guest_list: Optional[List[str]] = Field(None, description="主要宾客名单/身份（如：张总-客户CEO等）")
    purpose: str = Field(..., description="宴请目的: client（客户招待）/ partner（合作伙伴）/ investor（投资人关系）/ government（政府接待）/ internal（内部聚餐/团建）/ celebration（庆功/年会）/ interview（面试接待）/ other（其他）")

    # ── 预算 ──
    budget_per_person: float = Field(..., ge=0, description="人均预算（含酒水，元）")
    total_budget_ceiling: Optional[float] = Field(None, ge=0, description="总预算上限（元）")
    is_tax_deductible: Optional[bool] = Field(True, description="是否需可报销/开票")

    # ── 菜品偏好 ──
    cuisine_type: str = Field(..., description="菜系偏好: chinese（中餐）/ western（西餐）/ japanese（日料）/ korean（韩餐）/ fusion（融合菜）/ hotpot（火锅）/ cantonese（粤菜）/ sichuan（川菜）/ seafood（海鲜）/ barbecue（烧烤）/ other（其他）")
    cuisine_detail: Optional[str] = Field(None, description="菜品细节要求（如指定菜品/招牌菜等）")
    dietary_restrictions: Optional[str] = Field(None, description="饮食禁忌（过敏源、清真、素食、忌辣等）")

    # ── 酒水需求 ──
    wine_needs: str = Field("basic", description="酒水需求: none（不需要）/ basic（普通酒水）/ premium（精品酒水）/ luxury（高档名酒）")
    wine_type_preference: Optional[str] = Field(None, description="酒类偏好: baijiu（白酒）/ red_wine（红酒）/ white_wine（白葡萄酒）/ champagne（香槟）/ beer（啤酒）/ tea（茶饮）/ mixed（混合）")
    wine_budget_per_bottle: Optional[float] = Field(None, ge=0, description="单瓶酒水预算上限（元）")
    has_sommelier_needs: bool = Field(False, description="是否需要专业侍酒/品酒师推荐")

    # ── 地点时间 ──
    city: str = Field(..., description="所在城市")
    district: Optional[str] = Field(None, description="区域偏好")
    preferred_date: str = Field(..., description="用餐日期（YYYY-MM-DD）")
    preferred_time: str = Field("18:00", description="用餐时间（HH:MM）")
    is_flexible_time: bool = Field(True, description="时间是否可调")

    # ── 包间/环境 ──
    need_private_room: bool = Field(True, description="是否需要包间")
    private_room_size: Optional[str] = Field(None, description="包间规格: small（小包-6人）/ medium（中包-10人）/ large（大包-16人）/ VIP（豪华包）")
    atmosphere: Optional[str] = Field(None, description="环境氛围: elegant（高雅）/ warm（温馨）/ lively（热闹）/ business（商务）/ private（私密）")
    need_smoking_area: bool = Field(False, description="是否需要吸烟区/包间可吸烟")
    need_parking: bool = Field(True, description="是否需要停车场/代客泊车")

    # ── 附加服务 ──
    need_gifts: bool = Field(False, description="是否需要伴手礼/礼品准备")
    gift_type_preference: Optional[str] = Field(None, description="礼品偏好: company_gift（企业定制礼盒）/ local_specialty（本地特产）/ wine（酒）/ tea（茶）/ other（其他）")
    gift_budget_per_person: Optional[float] = Field(None, ge=0, description="礼品人均预算（元）")
    need_seating_chart: bool = Field(False, description="是否需要席位安排（主客座位排序）")
    has_speech_or_ceremony: bool = Field(False, description="是否有致辞/仪式环节")
    need_projection_av: bool = Field(False, description="是否需要投影/音响设备（如PPT展示）")
    special_requirements: Optional[str] = Field(None, description="特殊要求说明")
    notes: Optional[str] = Field(None, description="补充说明")

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v):
        valid = {"client", "partner", "investor", "government", "internal", "celebration", "interview", "other"}
        if v not in valid:
            raise ValueError(f"无效的宴请目的: {v}")
        return v

    @field_validator("guest_count")
    @classmethod
    def validate_guest_count(cls, v):
        if v > 50:
            raise ValueError(f"用餐人数超过50人: {v}，大型宴会请备注")
        return v

class CorporateProcurementParams(BaseModel):
    """企业采购参数"""
    company_name: str = Field(..., description="企业名称")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系人电话")
    contact_email: str = Field(..., description="联系邮箱")

    procurement_type: str = Field(..., description="采购类型")
    quantity: int = Field(..., description="采购数量")
    estimated_unit_price: float = Field(..., description="预估单价")
    total_budget: float = Field(..., description="总预算")

    delivery_city: str = Field(..., description="配送城市")
    delivery_address: str = Field(..., description="配送地址")
    need_installation: bool = Field(False, description="是否需要安装")

    preferred_brands: Optional[str] = Field(None, description="偏好品牌")
    quality_requirements: Optional[str] = Field(None, description="质量要求")

    delivery_deadline: str = Field(..., description="交付截止日期")
    is_urgent: bool = Field(False, description="是否加急")

    has_after_sales: bool = Field(False, description="是否需要售后服务")
    warranty_years: Optional[int] = Field(None, description="保修年限")

    payment_terms: str = Field(..., description="付款方式")
    need_invoice: bool = Field(False, description="是否需要发票")
    invoice_type: Optional[str] = Field(None, description="发票类型")

    need_quotations_count: int = Field(default=3, ge=1, le=10, description="至少需要几家报价")

    special_requirements: Optional[str] = Field(None, description="特殊要求")
    notes: Optional[str] = Field(None, description="备注")

    @field_validator("procurement_type")
    @classmethod
    def validate_procurement_type(cls, v):
        valid = {"office_supplies", "office_equipment", "it_hardware", "corporate_gifts", "furniture", "catering_supplies", "packaging_materials", "other"}
        if v not in valid:
            raise ValueError(f"无效的采购类型: {v}")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v > 1000:
            raise ValueError(f"数量 {v} 超过1000，请确认是否需要分批采购")
        return v

    @field_validator("payment_terms")
    @classmethod
    def validate_payment_terms(cls, v):
        valid = {"full_in_advance", "deposit_plus_balance", "net_30", "net_60"}
        if v not in valid:
            raise ValueError(f"无效的付款方式: {v}")
        return v

    @field_validator("invoice_type")
    @classmethod
    def validate_invoice_type(cls, v):
        if v is None:
            return v
        valid = {"普通发票", "增值税专用发票"}
        if v not in valid:
            raise ValueError(f"无效的发票类型: {v}")
        return v


class LogisticsDeliveryParams(BaseModel):
    """物流配送参数"""
    company_name: str = Field(..., description="公司名称")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系人电话")
    contact_email: str = Field(..., description="联系邮箱")

    delivery_type: str = Field(..., description="配送类型")
    item_description: str = Field(..., description="物品描述")
    item_value: float = Field(..., description="物品价值")

    item_weight_kg: float = Field(..., description="物品重量(kg)")
    item_dimensions: Optional[str] = Field(None, description="物品尺寸 长x宽x高cm")

    is_fragile: bool = Field(False, description="是否易碎")
    is_perishable: bool = Field(False, description="是否易腐")
    is_valuable: bool = Field(False, description="是否贵重")

    pickup_address: str = Field(..., description="取件地址")
    pickup_contact: str = Field(..., description="取件联系人")
    pickup_phone: str = Field(..., description="取件电话")

    delivery_address: str = Field(..., description="配送地址")
    delivery_contact: str = Field(..., description="收货联系人")
    delivery_phone: str = Field(..., description="收货电话")

    expected_pickup_date: str = Field(..., description="期望取件日期")
    expected_delivery_date: Optional[str] = Field(None, description="期望送达日期")

    is_urgent: bool = Field(False, description="是否加急")
    delivery_time_preference: str = Field(default="anytime", description="配送时间偏好")

    need_insurance: bool = Field(False, description="是否需要保险")
    insured_value: Optional[float] = Field(None, description="投保价值")

    need_signature: bool = Field(True, description="是否需要签收")

    payment_method: str = Field(..., description="付款方式")

    special_requirements: Optional[str] = Field(None, description="特殊要求")
    notes: Optional[str] = Field(None, description="备注")

    @field_validator("delivery_type")
    @classmethod
    def validate_delivery_type(cls, v):
        valid = {"document", "parcel", "cargo", "furniture_moving", "cold_chain", "international", "other"}
        if v not in valid:
            raise ValueError(f"无效的配送类型: {v}")
        return v

    @field_validator("item_weight_kg")
    @classmethod
    def validate_item_weight_kg(cls, v):
        if v > 10000:
            raise ValueError(f"重量 {v}kg 超过10000kg，建议走货运而非标准配送")
        return v

    @field_validator("delivery_time_preference")
    @classmethod
    def validate_delivery_time_preference(cls, v):
        valid = {"anytime", "morning", "afternoon", "evening", "weekend"}
        if v not in valid:
            raise ValueError(f"无效的配送时间偏好: {v}")
        return v

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v):
        valid = {"shipper_pay", "receiver_pay", "monthly_settlement"}
        if v not in valid:
            raise ValueError(f"无效的付款方式: {v}")
        return v


class SalesOutsourcingParams(BaseModel):
    """销售外包参数"""
    company_name: str = Field(..., description="公司名称")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系人电话")
    contact_email: str = Field(..., description="联系人邮箱")

    sales_type: str = Field(..., description="销售类型", pattern=r"^(telemarketing|field_sales|channel_development|exhibition|online_sales|after_sales|other)$")
    industry: str = Field(..., description="所属行业")
    target_customer_description: str = Field(..., description="目标客户描述")
    target_city_or_region: str = Field(..., description="目标城市或区域")

    team_size_required: int = Field(..., description="所需团队人数", ge=1)
    expected_duration_months: int = Field(..., description="预计合作时长（月）", ge=1)

    has_existing_customer_resources: bool = Field(..., description="是否已有客户资源")
    has_crm_system: bool = Field(..., description="是否有CRM系统")
    crm_system_name: Optional[str] = Field(None, description="CRM系统名称")

    product_or_service_description: str = Field(..., description="产品或服务描述")
    unit_price: Optional[float] = Field(None, description="单价", ge=0)

    sales_target_amount: float = Field(..., description="销售目标金额", ge=0)
    commission_rate_percent: Optional[float] = Field(None, description="佣金比例（%）", ge=0, le=100)

    payment_model: str = Field(..., description="付款模式", pattern=r"^(monthly_fee|commission_only|base_plus_commission|project_based)$")
    monthly_budget: float = Field(..., description="月度预算", ge=0)
    total_budget: Optional[float] = Field(None, description="总预算", ge=0)

    need_training: bool = Field(..., description="是否需要培训")
    training_days: Optional[int] = Field(None, description="培训天数", ge=1)

    need_reporting: bool = Field(..., description="是否需要报告")
    reporting_frequency: str = Field(..., description="报告频率", pattern=r"^(daily|weekly|biweekly|monthly)$")

    start_date: str = Field(..., description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")

    special_requirements: Optional[str] = Field(None, description="特殊要求")
    notes: Optional[str] = Field(None, description="备注")

    @field_validator("sales_type")
    @classmethod
    def validate_sales_type(cls, v: str) -> str:
        valid_types = {"telemarketing", "field_sales", "channel_development", "exhibition", "online_sales", "after_sales", "other"}
        if v not in valid_types:
            raise ValueError(f"无效的销售类型: {v}")
        return v

    @field_validator("team_size_required")
    @classmethod
    def validate_team_size(cls, v: int) -> int:
        if v > 50:
            print("提示: 团队人数超过50，建议考虑分多团队管理或分区域运作")
        return v


class EcommerceOperationsParams(BaseModel):
    """代运营/电商运营参数"""
    company_name: str = Field(..., description="公司名称")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系人电话")
    contact_email: str = Field(..., description="联系人邮箱")
    company_website: Optional[str] = Field(None, description="公司网站")

    platform: str = Field(..., description="电商平台", pattern=r"^(taobao|tmall|jd|pdd|douyin|xiaohongshu|kuaishou|weixin|amazon|shopify|multiple|other)$")
    store_url: Optional[str] = Field(None, description="店铺链接（如已有店铺）")
    store_age_months: Optional[int] = Field(None, description="店铺运营时长（月），0表示新店", ge=0)
    current_monthly_gmv: Optional[float] = Field(None, description="当前月GMV", ge=0)
    target_monthly_gmv: Optional[float] = Field(None, description="目标月GMV", ge=0)

    product_category: str = Field(..., description="产品类目")
    product_count: int = Field(..., description="产品数量", ge=1)

    operation_type: str = Field(..., description="运营类型", pattern=r"^(full_operation|content_marketing|livestream|short_video|seo_sem|customer_service|design|other)$")
    has_existing_content: bool = Field(..., description="是否有现有内容")
    content_count: Optional[int] = Field(None, description="现有内容数量", ge=0)

    need_content_creation: bool = Field(..., description="是否需要内容创作")
    content_type: str = Field(..., description="内容类型", pattern=r"^(video|article|image|live|mixed)$")

    team_size_needed: int = Field(..., description="所需团队人数", ge=1)
    expected_duration_months: int = Field(..., description="预计合作时长（月）", ge=1)

    monthly_budget_range_min: float = Field(..., description="月度预算下限", ge=0)
    monthly_budget_range_max: float = Field(..., description="月度预算上限", ge=0)

    kpi_focus: str = Field(..., description="KPI重点", pattern=r"^(sales|traffic|fans|conversion_rate|brand_awareness|mixed)$")
    has_brand_certification: bool = Field(..., description="是否有品牌认证")

    need_data_reporting: bool = Field(..., description="是否需要数据报告")
    reporting_frequency: str = Field(..., description="报告频率", pattern=r"^(daily|weekly|monthly)$")

    start_date: str = Field(..., description="开始日期")
    special_requirements: Optional[str] = Field(None, description="特殊要求")
    notes: Optional[str] = Field(None, description="备注")

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        valid_platforms = {"taobao", "tmall", "jd", "pdd", "douyin", "xiaohongshu", "kuaishou", "weixin", "amazon", "shopify", "multiple", "other"}
        if v not in valid_platforms:
            raise ValueError(f"无效的平台类型: {v}")
        return v

    @field_validator("operation_type")
    @classmethod
    def validate_operation_type(cls, v: str) -> str:
        valid_types = {"full_operation", "content_marketing", "livestream", "short_video", "seo_sem", "customer_service", "design", "other"}
        if v not in valid_types:
            raise ValueError(f"无效的运营类型: {v}")
        return v

    @field_validator("monthly_budget_range_max")
    @classmethod
    def validate_budget_range(cls, v: float, info) -> float:
        if "monthly_budget_range_min" in info.data and v < info.data["monthly_budget_range_min"]:
            raise ValueError("月度预算上限不能低于下限")
        return v


class RecruitmentOutsourcingParams(BaseModel):
    """猎头/招聘外包参数"""
    company_name: str = Field(..., description="公司名称")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系人电话")
    contact_email: str = Field(..., description="联系人邮箱")

    company_industry: str = Field(..., description="公司所属行业")
    company_size: str = Field(..., description="公司规模", pattern=r"^(startup|sme|mid_size|large|enterprise)$")

    recruitment_type: str = Field(..., description="招聘类型", pattern=r"^(executive_search|mid_level|bulk_hiring|rpo|temporary|other)$")
    position_title: str = Field(..., description="职位名称")
    department: str = Field(..., description="所属部门")
    report_to: Optional[str] = Field(None, description="汇报对象")

    headcount: int = Field(..., description="招聘人数", ge=1)
    work_city: str = Field(..., description="工作城市")
    work_address: Optional[str] = Field(None, description="工作详细地址")

    salary_range_min: float = Field(..., description="薪资范围下限", ge=0)
    salary_range_max: float = Field(..., description="薪资范围上限", ge=0)

    urgency: str = Field(..., description="紧急程度", pattern=r"^(urgent|normal|pipeline)$")
    key_requirements: str = Field(..., description="关键要求（技能描述）")
    education_requirement: Optional[str] = Field(None, description="学历要求")

    experience_years_min: int = Field(..., description="最低经验年限", ge=0)
    experience_years_max: Optional[int] = Field(None, description="最高经验年限", ge=0)

    age_preference_min: Optional[int] = Field(None, description="年龄偏好下限", ge=18)
    age_preference_max: Optional[int] = Field(None, description="年龄偏好上限", ge=18)

    gender_preference: str = Field(..., description="性别偏好", pattern=r"^(no_preference|male|female)$")
    has_team_to_manage: bool = Field(..., description="是否需要管理团队")
    team_size: Optional[int] = Field(None, description="管理团队规模", ge=1)

    need_confidential: bool = Field(..., description="是否需要保密")
    recruitment_deadline: str = Field(..., description="招聘截止日期")

    service_fee_model: str = Field(..., description="服务费模式", pattern=r"^(percentage_of_salary|fixed_fee|monthly_retainer|success_fee)$")
    percentage_rate: Optional[float] = Field(None, description="收费比例（%）", ge=0, le=100)

    special_requirements: Optional[str] = Field(None, description="特殊要求")
    notes: Optional[str] = Field(None, description="备注")

    @field_validator("recruitment_type")
    @classmethod
    def validate_recruitment_type(cls, v: str) -> str:
        valid_types = {"executive_search", "mid_level", "bulk_hiring", "rpo", "temporary", "other"}
        if v not in valid_types:
            raise ValueError(f"无效的招聘类型: {v}")
        return v

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        valid_urgencies = {"urgent", "normal", "pipeline"}
        if v not in valid_urgencies:
            raise ValueError(f"无效的紧急程度: {v}")
        return v

    @field_validator("gender_preference")
    @classmethod
    def validate_gender_preference(cls, v: str) -> str:
        valid_genders = {"no_preference", "male", "female"}
        if v not in valid_genders:
            raise ValueError(f"无效的性别偏好: {v}")
        return v

    @field_validator("salary_range_max")
    @classmethod
    def validate_salary_range(cls, v: float, info) -> float:
        if "salary_range_min" in info.data and v < info.data["salary_range_min"]:
            raise ValueError("薪资上限不能低于下限")
        return v

    @field_validator("experience_years_max")
    @classmethod
    def validate_experience_years(cls, v: Optional[int], info) -> Optional[int]:
        if v is not None and "experience_years_min" in info.data and v < info.data["experience_years_min"]:
            raise ValueError("最高经验年限不能低于最低经验年限")
        return v


class CorporateTrainingParams(BaseModel):
    """企业内训参数"""
    company_name: str = Field(..., description="企业名称")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系电话")
    contact_email: str = Field(..., description="联系邮箱")

    training_type: str = Field(..., description="培训类型")
    training_topic: str = Field(..., description="培训主题")
    training_objective: str = Field(..., description="培训目标")

    participant_count: int = Field(..., description="参训人数")
    participant_level: str = Field(..., description="参训级别")
    participant_department: Optional[str] = Field(None, description="参训部门")

    has_pre_training_assessment: bool = Field(..., description="是否需要训前调研")
    training_format: str = Field(..., description="培训形式")
    preferred_dates_start: str = Field(..., description="期望开始日期")
    preferred_dates_end: str = Field(..., description="期望结束日期")
    duration_days: int = Field(..., description="培训天数")
    hours_per_day: Optional[int] = Field(None, description="每天培训时长（小时）")

    preferred_city: Optional[str] = Field(None, description="首选城市")
    need_venue: bool = Field(..., description="是否需要场地")
    venue_requirements: Optional[str] = Field(None, description="场地要求")

    trainer_preference: str = Field(..., description="讲师偏好")
    trainer_name_recommendation: Optional[str] = Field(None, description="推荐讲师姓名")

    budget_per_session: float = Field(..., description="每场预算")
    total_budget: Optional[float] = Field(None, description="总预算")

    need_certification: bool = Field(..., description="是否需要证书")
    certification_name: Optional[str] = Field(None, description="证书名称")

    need_training_materials: bool = Field(..., description="是否需要培训资料")
    materials_type: str = Field(..., description="资料形式")
    need_post_training_assessment: bool = Field(..., description="是否需要训后评估")

    special_requirements: Optional[str] = Field(None, description="特殊要求")
    notes: Optional[str] = Field(None, description="备注")

    @field_validator("training_type")
    @classmethod
    def validate_training_type(cls, v: str) -> str:
        allowed = {"management", "leadership", "sales_skills", "customer_service", "technical", "soft_skills", "compliance", "team_building", "language", "other"}
        if v not in allowed:
            raise ValueError(f"无效的培训类型: {v}")
        return v

    @field_validator("training_format")
    @classmethod
    def validate_training_format(cls, v: str) -> str:
        allowed = {"in_person", "online", "hybrid", "workshop", "lecture"}
        if v not in allowed:
            raise ValueError(f"无效的培训形式: {v}")
        return v

    @field_validator("trainer_preference")
    @classmethod
    def validate_trainer_preference(cls, v: str) -> str:
        allowed = {"no_preference", "domestic_expert", "international_expert", "academic", "industry_practitioner"}
        if v not in allowed:
            raise ValueError(f"无效的讲师偏好: {v}")
        return v

    @field_validator("participant_level")
    @classmethod
    def validate_participant_level(cls, v: str) -> str:
        allowed = {"junior", "mid_level", "senior", "executive", "mixed"}
        if v not in allowed:
            raise ValueError(f"无效的参训级别: {v}")
        return v

    @field_validator("materials_type")
    @classmethod
    def validate_materials_type(cls, v: str) -> str:
        allowed = {"printed", "digital", "both"}
        if v not in allowed:
            raise ValueError(f"无效的资料形式: {v}")
        return v

    @field_validator("participant_count")
    @classmethod
    def validate_participant_count(cls, v: int) -> int:
        if v < 1:
            raise ValueError("参训人数必须大于0")
        if v > 100:
            raise ValueError(f"参训人数 {v}，超过100人建议分多场")
        return v


class ManufacturingSamplingParams(BaseModel):
    """代工/打样参数"""
    company_name: str = Field(..., description="企业名称")
    contact_name: str = Field(..., description="联系人姓名")
    contact_phone: str = Field(..., description="联系电话")
    contact_email: str = Field(..., description="联系邮箱")

    manufacturing_type: str = Field(..., description="制造类型")
    product_name: str = Field(..., description="产品名称")
    product_description: str = Field(..., description="产品描述")

    has_design_file: bool = Field(..., description="是否有设计文件")
    design_file_format: Optional[str] = Field(None, description="设计文件格式，如 CAD/STP/PDF/AI/PSD")
    has_sample_photo: bool = Field(..., description="是否有样品照片")

    material_requirements: str = Field(..., description="材料要求")
    process_requirements: Optional[str] = Field(None, description="工艺要求")

    quantity_min: int = Field(..., description="最小批量")
    quantity_max: Optional[int] = Field(None, description="最大批量")
    expected_unit_price_target: Optional[float] = Field(None, description="目标单价")

    quality_standard: str = Field(..., description="质量标准")
    need_certification: bool = Field(..., description="是否需要认证")
    certification_standard: Optional[str] = Field(None, description="认证标准")

    delivery_city: str = Field(..., description="交货城市")
    delivery_deadline: str = Field(..., description="交货截止日期")
    is_urgent: bool = Field(False, description="是否加急")

    need_design_support: bool = Field(..., description="是否需要设计支持")
    design_budget: Optional[float] = Field(None, description="设计预算")

    need_sample_first: bool = Field(..., description="是否需要先打样")
    sample_budget: Optional[float] = Field(None, description="打样预算")

    payment_terms: str = Field(..., description="付款方式")

    packaging_requirements: Optional[str] = Field(None, description="包装要求")
    sample_quantity: Optional[int] = Field(None, description="打样数量")

    special_requirements: Optional[str] = Field(None, description="特殊要求")
    notes: Optional[str] = Field(None, description="备注")

    @field_validator("manufacturing_type")
    @classmethod
    def validate_manufacturing_type(cls, v: str) -> str:
        allowed = {"electronics", "garment_apparel", "metal_fabrication", "plastic_molding", "packaging_printing", "chemical", "food_processing", "furniture", "toy", "other"}
        if v not in allowed:
            raise ValueError(f"无效的制造类型: {v}")
        return v

    @field_validator("quality_standard")
    @classmethod
    def validate_quality_standard(cls, v: str) -> str:
        allowed = {"standard", "premium", "custom"}
        if v not in allowed:
            raise ValueError(f"无效的质量标准: {v}")
        return v

    @field_validator("payment_terms")
    @classmethod
    def validate_payment_terms(cls, v: str) -> str:
        allowed = {"deposit_plus_balance", "net_30", "t_t", "l_c"}
        if v not in allowed:
            raise ValueError(f"无效的付款方式: {v}")
        return v

    @field_validator("quantity_min")
    @classmethod
    def validate_quantity_min(cls, v: int) -> int:
        if v < 1:
            raise ValueError("最小批量必须大于0")
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


# ── 团建策划 ──

CAPABILITIES_TEAM_BUILDING = {
    "status_machine": {
        "states": [
            {"id": "requirement_collection", "name": "需求收集", "description": "已接收团建需求，AI分析团队特征"},
            {"id": "scheme_design", "name": "方案设计", "description": "AI根据预算、人数、偏好生成推荐方案"},
            {"id": "scheme_confirmation", "name": "方案确认", "description": "客户确认方案细节"},
            {"id": "supplier_matching", "name": "供应商匹配", "description": "匹配场地/教练/物料供应商"},
            {"id": "booking", "name": "预订执行", "description": "确认场地、签约、付款"},
            {"id": "preparation", "name": "筹备阶段", "description": "物料准备、人员通知、交通安排"},
            {"id": "execution", "name": "活动执行", "description": "团建活动当日执行"},
            {"id": "settlement", "name": "结算确认", "description": "费用结算、满意度回访"},
            {"id": "completed", "name": "已完成", "description": "团建活动全部完成"},
        ],
        "transitions": [
            ["requirement_collection", "scheme_design"], ["scheme_design", "scheme_confirmation"],
            ["scheme_confirmation", "supplier_matching"], ["supplier_matching", "booking"],
            ["booking", "preparation"], ["preparation", "execution"],
            ["execution", "settlement"], ["settlement", "completed"],
            ["scheme_confirmation", "scheme_design"],  # 方案修改回退
        ],
    },
    "agent_auto": [
        {"id": "team_profile_analysis", "name": "团队特征分析", "description": "分析团队规模、年龄、构成，推荐匹配活动类型"},
        {"id": "activity_recommendation", "name": "活动智能推荐", "description": "根据多维度条件推荐最佳团建方案"},
        {"id": "budget_optimization", "name": "预算优化建议", "description": "在预算范围内推荐最优分配方案"},
        {"id": "supplier_comparison", "name": "供应商比价", "description": "自动比对各供应商价格和服务评价"},
        {"id": "timeline_planning", "name": "时间线规划", "description": "自动生成活动流程时间表和天气预报提醒"},
        {"id": "weather_check", "name": "天气预警", "description": "活动日前推送天气预报及应急预案建议"},
        {"id": "material_checklist", "name": "物料清单生成", "description": "自动生成物料清单和采购建议"},
        {"id": "insurance_calc", "name": "保险计算", "description": "根据活动类型计算保险需求并推荐"},
        {"id": "satisfaction_survey", "name": "满意度回访", "description": "活动结束后自动发送满意度问卷并分析"},
    ],
    "human_required": [
        {"id": "supplier_negotiation", "name": "供应商洽谈", "description": "与场地/供应商沟通具体执行细节"},
        {"id": "booking_confirmation", "name": "预订确认", "description": "付款、签约、确认预订"},
        {"id": "on_site_coordination", "name": "现场协调", "description": "活动当日现场驻场协调"},
        {"id": "photography", "name": "摄影摄像", "description": "活动跟拍及后期处理"},
        {"id": "transport_arrangement", "name": "交通安排", "description": "车辆调度和乘坐安排"},
        {"id": "material_purchase", "name": "物料采购", "description": "定制物料、奖牌、横幅等采购"},
    ],
    "escalation_conditions": [
        {"condition": "large_scale_over_100", "description": "团队超过100人，需大型场地和多个活动方案"},
        {"condition": "multi_day_trip", "description": "多日（2天以上）团建，涉及住宿和交通规划"},
        {"condition": "high_risk_activities", "description": "涉及高风险活动（攀岩、漂流、高空等），需额外保险和安全方案"},
        {"condition": "VIP_involved", "description": "有高管/客户参与，需更高接待标准"},
        {"condition": "special_equipment", "description": "需要特殊设备（如摄影器材、音响舞台等）"},
        {"condition": "cross_city", "description": "跨城市出行，涉及异地协作"},
    ],
    "knowledge_base": {
        "common_activity_types": {
            "outdoor_expansion": "户外拓展：适合20-100人，团队协作训练，含信任背摔/毕业墙等经典项目",
            "sports_competition": "体育运动：篮球/足球/羽毛球/趣味运动会，适合全年龄段",
            "creative_workshop": "创意工作坊：陶艺/烘焙/绘画/非遗手工，适合10-50人，轻松有趣",
            "escape_room": "密室逃脱：适合6-20人，分小组竞技，逻辑推理型",
            "board_games": "桌游：狼人杀/剧本杀/大富翁，适合10-30人室内轻松活动",
            "travel_outing": "出游旅行：郊游/登山/徒步，适合20-100人，需好天气",
            "charity": "公益活动：植树/支教/志愿服务，适合有社会责任感的企业",
        },
        "seasonal_recommendations": {
            "spring": "推荐：踏青/骑行/植树/风筝DIY",
            "summer": "推荐：水上运动/漂流/室内冰壶/密室",
            "autumn": "推荐：登山/采摘/露营/户外拓展",
            "winter": "推荐：温泉/滑雪/室内运动会/围炉煮茶",
        },
        "budget_guidelines": {
            "50-100": "人均50-100元：公园趣味运动/桌游/剧本杀",
            "100-200": "人均100-200元：室内拓展/创意工坊/密室逃脱",
            "200-500": "人均200-500元：户外拓展/主题团建/包场活动",
            "500+": "人均500元以上：多日出游/高端团建/定制方案",
        },
        "faq": [
            {"q": "团建一般提前多久预约？", "a": "建议提前1-2周，旺季（春秋季）建议提前3-4周。"},
            {"q": "天气不好怎么办？", "a": "签约前我们会准备A/B方案（室内外备选），活动前48小时根据天气预报最终确认。"},
            {"q": "保险怎么买？", "a": "我们的方案默认含活动意外险，高危项目单独购买专项保险。"},
        ],
    },
}


# ── 商务宴请 ──

CAPABILITIES_BUSINESS_DINING = {
    "status_machine": {
        "states": [
            {"id": "requirement_collection", "name": "需求收集", "description": "已接收宴请需求，AI分析接待规格"},
            {"id": "restaurant_recommendation", "name": "餐厅推荐", "description": "AI根据规格、预算、口味推荐3-5家方案"},
            {"id": "menu_design", "name": "菜单定制", "description": "根据预算和口味定制菜单方案"},
            {"id": "reservation", "name": "预订确认", "description": "预订包间、确认菜单、预付定金"},
            {"id": "special_arrangement", "name": "特殊安排", "description": "礼品准备、席位安排、设备调试"},
            {"id": "execution", "name": "宴请执行", "description": "用餐当日服务保障"},
            {"id": "settlement", "name": "结算反馈", "description": "费用结算、发票开具、满意度回访"},
            {"id": "completed", "name": "已完成", "description": "宴请全部完成"},
        ],
        "transitions": [
            ["requirement_collection", "restaurant_recommendation"],
            ["restaurant_recommendation", "menu_design"],
            ["menu_design", "reservation"],
            ["reservation", "special_arrangement"],
            ["special_arrangement", "execution"],
            ["execution", "settlement"],
            ["settlement", "completed"],
            ["restaurant_recommendation", "requirement_collection"],  # 重新推荐
        ],
    },
    "agent_auto": [
        {"id": "restaurant_recommendation", "name": "餐厅智能推荐", "description": "根据接待规格、菜系偏好、区域推荐最优餐厅"},
        {"id": "cuisine_pairing", "name": "菜品搭配建议", "description": "根据宾客身份和预算推荐菜式搭配"},
        {"id": "wine_pairing", "name": "酒水搭配推荐", "description": "根据菜品和接待规格推荐酒水搭配"},
        {"id": "budget_optimization", "name": "预算优化方案", "description": "在预算内推荐最优的菜品/酒水搭配方案"},
        {"id": "etiquette_reminder", "name": "商务礼仪提醒", "description": "根据接待对象和场景推送注意事项"},
        {"id": "seating_suggestion", "name": "席位建议", "description": "根据宾客身份推荐座次安排"},
        {"id": "gift_suggestion", "name": "伴手礼推荐", "description": "根据接待规格和地域推荐礼品方案"},
        {"id": "weather_traffic_alert", "name": "天气交通预警", "description": "推送当天天气、交通状况提醒"},
        {"id": "invoice_preparation", "name": "发票准备", "description": "提前确认开票信息，当天取发票"},
    ],
    "human_required": [
        {"id": "restaurant_negotiation", "name": "餐厅沟通协调", "description": "与餐厅确认特殊需求、包间布置、定制菜品"},
        {"id": "reservation_confirm", "name": "预订确认", "description": "支付押金、确认预订"},
        {"id": "special_menu_arrangement", "name": "定制菜单协调", "description": "和厨师长沟通特别需求"},
        {"id": "gift_preparation", "name": "礼品采购/准备", "description": "伴手礼采购、包装、派送"},
        {"id": "on_site_reception", "name": "现场接待协调", "description": "迎宾、引导、全程服务保障"},
    ],
    "escalation_conditions": [
        {"condition": "government_officials", "description": "接待政府官员，需考虑合规和廉政要求"},
        {"condition": "large_scale_over_20", "description": "超过20人的大型宴请，需宴会厅或多桌安排"},
        {"condition": "custom_menu_required", "description": "需要定制菜单（如主题宴、特殊菜品等）"},
        {"condition": "rare_cuisine", "description": "特殊菜系/稀缺餐厅，需要额外协调"},
        {"condition": "gift_with_branding", "description": "需要企业定制伴手礼，涉及包装设计和采购周期"},
        {"condition": "multi_table_seating", "description": "多桌宴请需要统筹席位安排和主客分配"},
    ],
    "knowledge_base": {
        "business_dining_etiquette": [
            "提前15-20分钟到餐厅，确认包间、菜单和酒水",
            "主人坐主位（面对包间门），主客坐主人右手边",
            "敬酒顺序：先长辈/领导，再平级",
            "菜品的上菜顺序：冷菜→主菜→热菜→汤→主食→甜点",
            "提前确认是否有饮食禁忌（清真、素食、过敏等）",
        ],
        "restaurant_grading": {
            "casual_dining": "便餐/简餐：人均50-150元，适合内部聚餐",
            "mid_range": "中档：人均150-400元，适合客户/合作伙伴招待",
            "high_end": "高档：人均400-800元，适合重要客户/投资人",
            "luxury": "豪华：人均800元以上，适合VIP/政府接待",
        },
        "common_wine_pairing": {
            "chinese": "中餐搭配白酒（茅台/五粮液）或黄酒",
            "western": "西餐红酒配红肉，白葡萄酒配白肉海鲜",
            "japanese": "日料搭配清酒或威士忌",
            "seafood": "海鲜配白葡萄酒或香槟",
        },
        "faq": [
            {"q": "商务宴请一般提前多久订？", "a": "建议提前3-5天，热门餐厅需提前1周。VIP级别建议提前1-2周。"},
            {"q": "不确定对方口味怎么办？", "a": "推荐融合菜/粤菜，口味中和，接受度高。也可提前沟通菜单征求意见。"},
            {"q": "需要开发票报销吗？", "a": "默认提供发票。下单时请填写开票信息。"},
            {"q": "万一需要取消怎么办？", "a": "一般提前24小时可免费取消，当天取消可能产生费用。"},
        ],
    },
}


CAPABILITIES_CORPORATE_PROCUREMENT = {
    "status_machine": {
        "states": [
            {
                "id": "requirement_collection",
                "name": "需求收集",
                "description": "收集企业采购需求信息"
            },
            {
                "id": "supplier_matching",
                "name": "供应商匹配",
                "description": "根据需求匹配合适供应商"
            },
            {
                "id": "quotation_comparison",
                "name": "报价对比",
                "description": "对比多家供应商报价"
            },
            {
                "id": "negotiation",
                "name": "商务谈判",
                "description": "与供应商进行价格和条款谈判"
            },
            {
                "id": "order_confirmation",
                "name": "订单确认",
                "description": "确认采购订单并签约"
            },
            {
                "id": "delivery_tracking",
                "name": "物流跟踪",
                "description": "跟踪采购物品的物流状态"
            },
            {
                "id": "acceptance_check",
                "name": "验收检查",
                "description": "对到货物资进行验收"
            },
            {
                "id": "settlement",
                "name": "结算付款",
                "description": "完成采购结算和付款"
            }
        ],
        "transitions": [
            [
                "requirement_collection",
                "supplier_matching"
            ],
            [
                "supplier_matching",
                "quotation_comparison"
            ],
            [
                "quotation_comparison",
                "negotiation"
            ],
            [
                "negotiation",
                "order_confirmation"
            ],
            [
                "order_confirmation",
                "delivery_tracking"
            ],
            [
                "delivery_tracking",
                "acceptance_check"
            ],
            [
                "acceptance_check",
                "settlement"
            ],
            [
                "negotiation",
                "quotation_comparison"
            ],
            [
                "order_confirmation",
                "negotiation"
            ]
        ]
    },
    "agent_auto": [
        {
            "id": "requirement_analysis",
            "name": "需求分析",
            "description": "AI自动分析采购需求并生成需求文档"
        },
        {
            "id": "supplier_search",
            "name": "供应商搜索",
            "description": "AI自动搜索和筛选潜在供应商"
        },
        {
            "id": "quotation_comparison",
            "name": "报价对比",
            "description": "AI自动对比多家供应商报价并生成对比表"
        },
        {
            "id": "price_analysis",
            "name": "价格分析",
            "description": "AI自动分析市场价格趋势和历史价格数据"
        },
        {
            "id": "delivery_tracking",
            "name": "物流跟踪",
            "description": "AI自动跟踪订单物流状态并更新"
        },
        {
            "id": "invoice_verification",
            "name": "发票核验",
            "description": "AI自动核验发票真伪和信息准确性"
        },
        {
            "id": "feedback_collection",
            "name": "反馈收集",
            "description": "AI自动收集供应商履约反馈和评分"
        }
    ],
    "human_required": [
        {
            "id": "supplier_negotiation",
            "name": "供应商谈判",
            "description": "人工与供应商进行价格和条款的商务谈判"
        },
        {
            "id": "contract_signing",
            "name": "合同签署",
            "description": "人工审核并签署正式采购合同"
        },
        {
            "id": "quality_inspection",
            "name": "质量检验",
            "description": "人工对到货产品进行质量检验和测试"
        },
        {
            "id": "acceptance_signoff",
            "name": "验收签收",
            "description": "人工确认验收结果并签署验收单据"
        },
        {
            "id": "payment_execution",
            "name": "付款执行",
            "description": "人工执行付款审批流程并完成付款"
        }
    ],
    "escalation_conditions": [
        {
            "condition": "budget_overrun_over_20pct",
            "description": "预算超支超过20%时升级人工处理"
        },
        {
            "condition": "single_source_procurement",
            "description": "单一来源采购需合规审批时升级人工处理"
        },
        {
            "condition": "quality_dispute",
            "description": "出现质量争议无法达成一致时升级人工处理"
        },
        {
            "condition": "delayed_delivery_over_7days",
            "description": "交货延迟超过7天时升级人工处理"
        },
        {
            "condition": "special_high_value_item",
            "description": "特殊高价值物品采购需人工审核时升级人工处理"
        }
    ],
    "knowledge_base": {
        "procurement_types_comparison": [
            "公开招标：适用于大额标准化采购，流程透明",
            "邀请招标：适用于特定供应商，效率较高",
            "竞争性谈判：适用于紧急或复杂需求",
            "单一来源：适用于专利或独家产品",
            "询价采购：适用于小额标准化商品"
        ],
        "common_office_supplies_brands": [
            "办公文具：晨光、得力、齐心、广博",
            "办公设备：惠普、佳能、兄弟、爱普生",
            "办公家具：震旦、圣奥、美时、冠美",
            "IT设备：联想、戴尔、华为、苹果"
        ],
        "payment_terms_explanation": [
            "预付：合同签订后支付30%-50%定金",
            "货到付款：收到货物后支付全款",
            "月结：每月固定日期结算上月货款",
            "账期：30天/60天/90天账期结算",
            "分期付款：按项目里程碑分批支付"
        ],
        "negotiation_tips": [
            "提前了解市场价格基准",
            "设定明确的谈判底线和目标价",
            "利用多家报价进行比价谈判",
            "关注总拥有成本而非单价",
            "建立长期合作关系的谈判策略"
        ]
    }
}

CAPABILITIES_LOGISTICS_DELIVERY = {
    "status_machine": {
        "states": [
            {
                "id": "requirement_collection",
                "name": "需求收集",
                "description": "收集发货需求和货物信息"
            },
            {
                "id": "carrier_matching",
                "name": "承运商匹配",
                "description": "根据货物匹配合适承运商"
            },
            {
                "id": "booking",
                "name": "预约下单",
                "description": "预约承运商并下单运输"
            },
            {
                "id": "pickup",
                "name": "上门取件",
                "description": "安排承运商上门取件"
            },
            {
                "id": "in_transit",
                "name": "运输中",
                "description": "货物在途运输状态跟踪"
            },
            {
                "id": "delivery",
                "name": "派送中",
                "description": "到达目的地城市进行末端派送"
            },
            {
                "id": "confirmation",
                "name": "签收确认",
                "description": "收件人签收确认"
            },
            {
                "id": "settlement",
                "name": "费用结算",
                "description": "完成运输费用结算"
            }
        ],
        "transitions": [
            [
                "requirement_collection",
                "carrier_matching"
            ],
            [
                "carrier_matching",
                "booking"
            ],
            [
                "booking",
                "pickup"
            ],
            [
                "pickup",
                "in_transit"
            ],
            [
                "in_transit",
                "delivery"
            ],
            [
                "delivery",
                "confirmation"
            ],
            [
                "confirmation",
                "settlement"
            ],
            [
                "in_transit",
                "delivery"
            ]
        ]
    },
    "agent_auto": [
        {
            "id": "route_optimization",
            "name": "路线优化",
            "description": "AI自动优化运输路线提高效率"
        },
        {
            "id": "carrier_comparison",
            "name": "承运商对比",
            "description": "AI自动对比各承运商价格和服务"
        },
        {
            "id": "tracking_push",
            "name": "物流推送",
            "description": "AI自动推送物流状态更新给相关方"
        },
        {
            "id": "eta_prediction",
            "name": "预计到达预测",
            "description": "AI自动预测货物预计到达时间"
        },
        {
            "id": "cost_estimation",
            "name": "费用估算",
            "description": "AI自动估算运输费用"
        },
        {
            "id": "document_generation",
            "name": "单证生成",
            "description": "AI自动生成运输单据和报关文件"
        },
        {
            "id": "delivery_confirmation",
            "name": "送达确认",
            "description": "AI自动确认送达并生成签收记录"
        }
    ],
    "human_required": [
        {
            "id": "fragile_item_handling",
            "name": "易碎品处理",
            "description": "人工处理易碎品的特殊包装和搬运"
        },
        {
            "id": "customs_clearance",
            "name": "报关清关",
            "description": "人工处理进出口报关清关手续"
        },
        {
            "id": "emergency_replanning",
            "name": "紧急重新规划",
            "description": "人工处理突发情况重新规划运输方案"
        },
        {
            "id": "special_cargo_handling",
            "name": "特殊货物处理",
            "description": "人工处理超大超重或特殊货物的装卸"
        },
        {
            "id": "on_site_coordination",
            "name": "现场协调",
            "description": "人工协调现场装卸和多方交接"
        }
    ],
    "escalation_conditions": [
        {
            "condition": "item_damage_or_loss",
            "description": "货物损坏或丢失时升级人工处理"
        },
        {
            "condition": "customs_hold",
            "description": "海关扣留或查验时升级人工处理"
        },
        {
            "condition": "address_change_en_route",
            "description": "运输途中地址变更时升级人工处理"
        },
        {
            "condition": "weather_delay",
            "description": "恶劣天气导致运输延迟时升级人工处理"
        },
        {
            "condition": "dangerous_goods",
            "description": "危险品运输需特殊审批时升级人工处理"
        }
    ],
    "knowledge_base": {
        "carrier_types_comparison": [
            "快递：适合小件包裹，时效快，门到门服务",
            "零担：适合中等批量货物，按吨位计费",
            "整车：适合大批量货物，整车直达运输",
            "海运：适合大宗货物跨国运输，成本低",
            "空运：适合高价值急件，速度最快",
            "铁路：适合内陆大宗货物，性价比高"
        ],
        "packaging_guidelines_by_item_type": [
            "电子产品：防静电包装+缓冲材料+防潮",
            "易碎品：气泡膜+泡沫填充+外箱加固",
            "液体物品：密封包装+防漏处理+标识",
            "大件物品：木箱加固+固定绑带+防护角",
            "文件证件：防水袋+硬纸板夹层保护"
        ],
        "insurance_types": [
            "基本险：承保运输工具受损导致的货物损失",
            "综合险：承保基本险外加自然灾害损失",
            "一切险：承保所有意外风险，保障最全面",
            "战争险：承保战争冲突导致的货物损失",
            "罢工险：承保罢工暴动导致的货物损失"
        ],
        "international_shipping_docs": [
            "商业发票：货物价值、数量、品名等详细信息",
            "装箱单：每箱货物的详细清单和尺寸重量",
            "原产地证明：货物原产地证明文件",
            "提单/空运单：运输合同和物权凭证",
            "报关委托书：委托报关行办理报关手续",
            "保险单：货物运输保险凭证"
        ]
    }
}

CAPABILITIES_SALES_OUTSOURCING = {
    "status_machine": {
        "states": [
            {
                "id": "requirement_collection",
                "name": "需求收集",
                "description": "收集客户销售外包需求"
            },
            {
                "id": "team_matching",
                "name": "团队匹配",
                "description": "匹配合适的销售团队"
            },
            {
                "id": "contract_signing",
                "name": "合同签署",
                "description": "签署销售外包服务合同"
            },
            {
                "id": "team_onboarding",
                "name": "团队入职",
                "description": "销售团队入职和培训"
            },
            {
                "id": "execution",
                "name": "执行阶段",
                "description": "销售团队执行销售任务"
            },
            {
                "id": "reporting",
                "name": "报告汇报",
                "description": "定期汇报销售进展和数据"
            },
            {
                "id": "performance_review",
                "name": "绩效评估",
                "description": "对销售团队进行绩效评估"
            },
            {
                "id": "settlement",
                "name": "结算付款",
                "description": "完成费用结算和佣金支付"
            }
        ],
        "transitions": [
            [
                "requirement_collection",
                "team_matching"
            ],
            [
                "team_matching",
                "contract_signing"
            ],
            [
                "contract_signing",
                "team_onboarding"
            ],
            [
                "team_onboarding",
                "execution"
            ],
            [
                "execution",
                "reporting"
            ],
            [
                "reporting",
                "performance_review"
            ],
            [
                "performance_review",
                "settlement"
            ],
            [
                "performance_review",
                "execution"
            ],
            [
                "execution",
                "execution"
            ]
        ]
    },
    "agent_auto": [
        {
            "id": "requirement_analysis",
            "name": "需求分析",
            "description": "AI自动分析客户销售外包需求"
        },
        {
            "id": "team_recommendation",
            "name": "团队推荐",
            "description": "AI自动推荐匹配的销售团队"
        },
        {
            "id": "kpi_setting",
            "name": "KPI设定",
            "description": "AI自动设定销售KPI指标"
        },
        {
            "id": "progress_tracking",
            "name": "进度跟踪",
            "description": "AI自动跟踪销售任务完成进度"
        },
        {
            "id": "report_generation",
            "name": "报告生成",
            "description": "AI自动生成销售进展报告"
        },
        {
            "id": "performance_analysis",
            "name": "绩效分析",
            "description": "AI自动分析团队绩效数据"
        },
        {
            "id": "commission_calc",
            "name": "佣金计算",
            "description": "AI自动计算销售佣金和提成"
        }
    ],
    "human_required": [
        {
            "id": "team_interview",
            "name": "团队面试",
            "description": "人工面试评估销售团队的适配度"
        },
        {
            "id": "training_delivery",
            "name": "培训交付",
            "description": "人工对销售团队进行产品和技能培训"
        },
        {
            "id": "customer_handover",
            "name": "客户交接",
            "description": "人工完成现有客户资源的交接工作"
        },
        {
            "id": "dispute_resolution",
            "name": "争议处理",
            "description": "人工处理销售过程中的客户争议"
        },
        {
            "id": "contract_renewal",
            "name": "合同续签",
            "description": "人工跟进合同到期续签事宜"
        }
    ],
    "escalation_conditions": [
        {
            "condition": "poor_performance_2consecutive_months",
            "description": "连续两个月绩效不达标时升级人工处理"
        },
        {
            "condition": "customer_complaint",
            "description": "出现客户正式投诉时升级人工处理"
        },
        {
            "condition": "staff_turnover",
            "description": "销售团队人员离职变动时升级人工处理"
        },
        {
            "condition": "budget_exceeded",
            "description": "预算超支需调整方案时升级人工处理"
        },
        {
            "condition": "scope_change",
            "description": "服务范围变更需重新协商时升级人工处理"
        },
        {
            "condition": "contract_termination",
            "description": "需要提前终止合同时升级人工处理"
        }
    ],
    "knowledge_base": {
        "sales_outsourcing_models": [
            "全外包模式：客户完全委托销售团队执行",
            "半外包模式：客户自有团队与外包团队配合",
            "项目制模式：按特定项目或产品线外包",
            "区域承包模式：按地理区域委托销售",
            "渠道开拓模式：专注于新渠道开发的外包"
        ],
        "typical_kpis_by_industry": [
            "SaaS行业：MQL数量、SQL转化率、ARR增长率",
            "消费品行业：铺货率、动销率、回转率",
            "制造业：订单金额、新客户数、回款率",
            "金融行业：AUM规模、客户转化率、交叉销售率"
        ],
        "commission_rate_benchmarks": [
            "标准产品销售：销售额的5%-15%",
            "高附加值产品：销售额的15%-30%",
            "SaaS订阅：首年合同额的20%-40%",
            "大客户销售：阶梯式佣金，超目标额外奖励",
            "渠道销售：分销差价+返点奖励机制"
        ],
        "contract_template": [
            "服务范围与交付物定义",
            "KPI指标与考核标准",
            "佣金结构与结算方式",
            "保密协议与竞业限制",
            "违约责任与终止条款",
            "争议解决机制"
        ]
    }
}

CAPABILITIES_ECOMMERCE_OPERATIONS = {
    "status_machine": {
        "states": [
            {
                "id": "requirement_collection",
                "name": "需求收集",
                "description": "收集电商代运营需求"
            },
            {
                "id": "platform_analysis",
                "name": "平台分析",
                "description": "分析目标平台特性和竞争环境"
            },
            {
                "id": "strategy_design",
                "name": "策略设计",
                "description": "设计运营策略和营销方案"
            },
            {
                "id": "contract_signing",
                "name": "合同签署",
                "description": "签署代运营服务合同"
            },
            {
                "id": "team_setup",
                "name": "团队组建",
                "description": "组建专属运营团队"
            },
            {
                "id": "content_creation",
                "name": "内容制作",
                "description": "制作商品详情和营销素材"
            },
            {
                "id": "operation_execution",
                "name": "运营执行",
                "description": "执行日常运营和推广活动"
            },
            {
                "id": "data_reporting",
                "name": "数据报告",
                "description": "输出运营数据分析报表"
            },
            {
                "id": "settlement",
                "name": "结算付款",
                "description": "完成运营服务费用结算"
            }
        ],
        "transitions": [
            [
                "requirement_collection",
                "platform_analysis"
            ],
            [
                "platform_analysis",
                "strategy_design"
            ],
            [
                "strategy_design",
                "contract_signing"
            ],
            [
                "contract_signing",
                "team_setup"
            ],
            [
                "team_setup",
                "content_creation"
            ],
            [
                "content_creation",
                "operation_execution"
            ],
            [
                "operation_execution",
                "data_reporting"
            ],
            [
                "data_reporting",
                "operation_execution"
            ],
            [
                "operation_execution",
                "settlement"
            ]
        ]
    },
    "agent_auto": [
        {
            "id": "competitor_analysis",
            "name": "竞品分析",
            "description": "AI自动分析竞争对手的运营策略"
        },
        {
            "id": "keyword_research",
            "name": "关键词研究",
            "description": "AI自动挖掘和优化搜索关键词"
        },
        {
            "id": "content_planning",
            "name": "内容规划",
            "description": "AI自动规划内容发布日历和主题"
        },
        {
            "id": "seo_audit",
            "name": "SEO诊断",
            "description": "AI自动进行搜索引擎优化诊断"
        },
        {
            "id": "data_dashboard",
            "name": "数据看板",
            "description": "AI自动生成运营数据可视化看板"
        },
        {
            "id": "ad_optimization",
            "name": "广告优化",
            "description": "AI自动优化广告投放策略和出价"
        },
        {
            "id": "inventory_alert",
            "name": "库存预警",
            "description": "AI自动监测库存并发出补货预警"
        },
        {
            "id": "performance_report",
            "name": "绩效报告",
            "description": "AI自动生成运营绩效报告"
        }
    ],
    "human_required": [
        {
            "id": "strategy_approval",
            "name": "策略审批",
            "description": "人工审核并批准运营策略方案"
        },
        {
            "id": "content_review",
            "name": "内容审核",
            "description": "人工审核营销内容的准确性和合规性"
        },
        {
            "id": "live_stream_hosting",
            "name": "直播带货",
            "description": "人工进行直播带货和互动"
        },
        {
            "id": "customer_service_escalation",
            "name": "客服升级",
            "description": "人工处理升级的客户投诉和纠纷"
        },
        {
            "id": "supplier_communication",
            "name": "供应商沟通",
            "description": "人工与供应商沟通库存和供货问题"
        }
    ],
    "escalation_conditions": [
        {
            "condition": "platform_penalty",
            "description": "平台处罚或违规警告时升级人工处理"
        },
        {
            "condition": "account_suspension",
            "description": "账号被平台暂停或限制时升级人工处理"
        },
        {
            "condition": "negative_review_crisis",
            "description": "差评暴增或负面舆情危机时升级人工处理"
        },
        {
            "condition": "gmv_drop_over_30pct",
            "description": "GMV环比下降超过30%时升级人工处理"
        },
        {
            "condition": "budget_overrun",
            "description": "营销预算超支需调整时升级人工处理"
        },
        {
            "condition": "brand_reputation_crisis",
            "description": "品牌声誉遭受重大危机时升级人工处理"
        }
    ],
    "knowledge_base": {
        "platform_comparison": [
            "淘宝天猫：流量大，适合品牌旗舰店，工具丰富",
            "京东：品质信赖度高，物流体验好，客单价高",
            "拼多多：下沉市场，社交裂变，性价比导向",
            "抖音电商：内容驱动，兴趣推荐，转化路径短",
            "小红书：种草社区，年轻女性用户，口碑营销",
            "亚马逊：跨境电商首选，全球覆盖，规则严格"
        ],
        "traffic_sources_by_platform": [
            "搜索流量：关键词优化和搜索广告",
            "推荐流量：平台算法推荐和个性化展示",
            "内容流量：短视频、直播、图文内容",
            "社交流量：社群分享和社交裂变",
            "付费流量：直通车、钻展、信息流广告"
        ],
        "content_types_by_platform": [
            "主图视频：商品核心卖点展示，15-30秒",
            "详情页：产品参数和优势深度说明",
            "买家秀：真实用户评价和晒图",
            "短视频：品牌故事和使用场景展示",
            "直播：实时互动带货和限时优惠",
            "种草笔记：KOL/KOC体验分享和推荐"
        ],
        "kpi_benchmarks_by_industry": [
            "服饰行业：点击率>3%，转化率>2%，客单价200-500元",
            "美妆行业：点击率>4%，转化率>3%，复购率>20%",
            "食品行业：点击率>2.5%，转化率>4%，客单价50-150元",
            "3C数码：点击率>2%，转化率>1.5%，客单价500-2000元",
            "家居行业：点击率>2.5%，转化率>2.5%，客单价100-500元"
        ]
    }
}

CAPABILITIES_RECRUITMENT_OUTSOURCING = {
    "status_machine": {
        "states": [
            {
                "id": "requirement_collection",
                "name": "需求收集",
                "description": "收集客户招聘需求信息"
            },
            {
                "id": "position_analysis",
                "name": "职位分析",
                "description": "分析职位要求和市场人才情况"
            },
            {
                "id": "candidate_search",
                "name": "候选人搜索",
                "description": "多渠道搜索和挖掘候选人"
            },
            {
                "id": "screening",
                "name": "简历筛选",
                "description": "筛选符合条件的候选人简历"
            },
            {
                "id": "interview_arrangement",
                "name": "面试安排",
                "description": "安排候选人与客户面试"
            },
            {
                "id": "offer_management",
                "name": "Offer管理",
                "description": "管理录用通知和薪资谈判"
            },
            {
                "id": "onboarding",
                "name": "入职跟进",
                "description": "跟进候选人入职流程"
            },
            {
                "id": "probation_review",
                "name": "试用期评估",
                "description": "评估候选人的试用期表现"
            },
            {
                "id": "settlement",
                "name": "费用结算",
                "description": "完成招聘服务费用结算"
            }
        ],
        "transitions": [
            [
                "requirement_collection",
                "position_analysis"
            ],
            [
                "position_analysis",
                "candidate_search"
            ],
            [
                "candidate_search",
                "screening"
            ],
            [
                "screening",
                "interview_arrangement"
            ],
            [
                "interview_arrangement",
                "offer_management"
            ],
            [
                "offer_management",
                "onboarding"
            ],
            [
                "onboarding",
                "probation_review"
            ],
            [
                "probation_review",
                "settlement"
            ],
            [
                "screening",
                "candidate_search"
            ],
            [
                "offer_management",
                "interview_arrangement"
            ]
        ]
    },
    "agent_auto": [
        {
            "id": "requirement_analysis",
            "name": "需求分析",
            "description": "AI自动分析招聘需求和岗位画像"
        },
        {
            "id": "resume_screening",
            "name": "简历筛选",
            "description": "AI自动筛选匹配度高的候选人简历"
        },
        {
            "id": "candidate_matching",
            "name": "候选人匹配",
            "description": "AI自动匹配最适合的候选人推荐"
        },
        {
            "id": "interview_scheduling",
            "name": "面试排期",
            "description": "AI自动协调面试时间安排"
        },
        {
            "id": "market_salary_analysis",
            "name": "市场薪酬分析",
            "description": "AI自动分析岗位市场薪酬水平"
        },
        {
            "id": "background_check_initiation",
            "name": "背调发起",
            "description": "AI自动发起候选人背景调查流程"
        },
        {
            "id": "progress_reporting",
            "name": "进度报告",
            "description": "AI自动生成招聘进展报告"
        }
    ],
    "human_required": [
        {
            "id": "candidate_interview",
            "name": "候选人面试",
            "description": "人工面试评估候选人能力和适配度"
        },
        {
            "id": "offer_negotiation",
            "name": "Offer谈判",
            "description": "人工与候选人进行薪资待遇谈判"
        },
        {
            "id": "reference_check",
            "name": "背景核实",
            "description": "人工进行候选人履历背景核实"
        },
        {
            "id": "onboarding_coordination",
            "name": "入职协调",
            "description": "人工协调候选人入职手续和准备工作"
        },
        {
            "id": "client_communication",
            "name": "客户沟通",
            "description": "人工与客户保持沟通反馈招聘进展"
        }
    ],
    "escalation_conditions": [
        {
            "condition": "no_qualified_candidate_30days",
            "description": "30天内未找到合适的候选人时升级人工处理"
        },
        {
            "condition": "offer_rejected_2times",
            "description": "候选人连续两次拒绝Offer时升级人工处理"
        },
        {
            "condition": "counter_offer_situation",
            "description": "候选人收到原公司挽留Offer时升级人工处理"
        },
        {
            "condition": "salary_expectation_mismatch",
            "description": "候选人与客户薪资期望差距过大时升级人工处理"
        },
        {
            "condition": "confidentiality_breach",
            "description": "出现信息泄露或保密违规时升级人工处理"
        }
    ],
    "knowledge_base": {
        "recruitment_channels_comparison": [
            "猎聘网：中高端人才，行业覆盖广，响应较快",
            "LinkedIn：外企和高端职位，国际化人才库",
            "Boss直聘：直接沟通，效率高，年轻人才多",
            "智联招聘：综合平台，各层次人才覆盖",
            "脉脉：社交招聘，人脉推荐，行业私密沟通",
            "内部推荐：Quality最高，留存率最高，成本适中"
        ],
        "interview_types": [
            "结构化面试：标准化问题，评分客观，适合批量面试",
            "行为面试：STAR法则，考察过往行为表现",
            "案例面试：商业案例分析，考察逻辑思维",
            "技术面试：代码测试或技术问答，考察专业能力",
            "无领导小组：群面形式，考察团队协作和领导力",
            "压力面试：高强度提问，考察抗压能力"
        ],
        "salary_benchmarks_by_level": [
            "初级(1-3年)：月薪8K-15K，年薪10-20万",
            "中级(3-5年)：月薪15K-25K，年薪20-35万",
            "高级(5-8年)：月薪25K-40K，年薪35-55万",
            "专家/经理(8-10年)：月薪40K-60K，年薪55-80万",
            "总监级(10年以上)：年薪80-150万+期权股票"
        ],
        "offer_negotiation_tips": [
            "了解候选人真实离职动机和优先级",
            "准备完整的薪酬包方案而非仅谈薪资",
            "强调职业发展空间和企业文化优势",
            "适时给出决策时间压力促进签约",
            "保持诚信透明的沟通建立信任"
        ]
    }
}

CAPABILITIES_CORPORATE_TRAINING = {
    "status_machine": {
        "states": [
            {
                "id": "requirement_collection",
                "name": "需求收集",
                "description": "收集企业培训需求信息"
            },
            {
                "id": "needs_assessment",
                "name": "需求评估",
                "description": "评估培训需求和能力差距"
            },
            {
                "id": "trainer_matching",
                "name": "讲师匹配",
                "description": "匹配合适的培训讲师"
            },
            {
                "id": "program_design",
                "name": "方案设计",
                "description": "设计培训课程方案"
            },
            {
                "id": "contract_signing",
                "name": "合同签署",
                "description": "签署培训服务合同"
            },
            {
                "id": "training_execution",
                "name": "培训实施",
                "description": "执行培训课程"
            },
            {
                "id": "evaluation",
                "name": "效果评估",
                "description": "评估培训效果和反馈"
            },
            {
                "id": "settlement",
                "name": "费用结算",
                "description": "完成培训费用结算"
            }
        ],
        "transitions": [
            [
                "requirement_collection",
                "needs_assessment"
            ],
            [
                "needs_assessment",
                "trainer_matching"
            ],
            [
                "trainer_matching",
                "program_design"
            ],
            [
                "program_design",
                "contract_signing"
            ],
            [
                "contract_signing",
                "training_execution"
            ],
            [
                "training_execution",
                "evaluation"
            ],
            [
                "evaluation",
                "settlement"
            ],
            [
                "program_design",
                "trainer_matching"
            ],
            [
                "evaluation",
                "training_execution"
            ]
        ]
    },
    "agent_auto": [
        {
            "id": "needs_assessment_analysis",
            "name": "需求评估分析",
            "description": "AI自动分析培训需求并评估能力差距"
        },
        {
            "id": "trainer_recommendation",
            "name": "讲师推荐",
            "description": "AI自动推荐匹配的培训讲师"
        },
        {
            "id": "curriculum_design",
            "name": "课程设计",
            "description": "AI自动设计培训课程大纲和内容"
        },
        {
            "id": "material_generation",
            "name": "素材生成",
            "description": "AI自动生成培训课件和辅助材料"
        },
        {
            "id": "evaluation_report",
            "name": "评估报告",
            "description": "AI自动生成培训效果评估报告"
        },
        {
            "id": "cost_estimation",
            "name": "成本估算",
            "description": "AI自动估算培训方案成本"
        },
        {
            "id": "feedback_collection",
            "name": "反馈收集",
            "description": "AI自动收集和分析学员反馈"
        }
    ],
    "human_required": [
        {
            "id": "trainer_interview",
            "name": "讲师面试",
            "description": "人工面试评估培训讲师的资质和能力"
        },
        {
            "id": "custom_training_delivery",
            "name": "定制化授课",
            "description": "人工讲师进行定制化课程授课"
        },
        {
            "id": "on_site_logistics",
            "name": "现场会务",
            "description": "人工负责培训现场的会务和组织工作"
        },
        {
            "id": "participant_engagement",
            "name": "学员互动",
            "description": "人工引导学员参与和课堂互动"
        },
        {
            "id": "certification_issuance",
            "name": "证书颁发",
            "description": "人工审核和颁发培训结业证书"
        }
    ],
    "escalation_conditions": [
        {
            "condition": "trainer_cancellation",
            "description": "讲师临时取消课程时升级人工处理"
        },
        {
            "condition": "insufficient_participants",
            "description": "报名人数不足开班标准时升级人工处理"
        },
        {
            "condition": "venue_issue",
            "description": "培训场地出现突发问题时升级人工处理"
        },
        {
            "condition": "quality_dissatisfaction",
            "description": "学员对培训质量不满投诉时升级人工处理"
        },
        {
            "condition": "budget_overrun",
            "description": "培训预算超支需调整方案时升级人工处理"
        }
    ],
    "knowledge_base": {
        "training_types_comparison": [
            "公开课：多人参加，成本分摊，适合通用技能",
            "企业内训：专属定制，针对性强，适合特定需求",
            "线上培训：灵活便捷，可回放，适合理论课程",
            "混合式培训：线上+线下结合，效果最佳",
            "工作坊：实操互动，解决实际问题，适合管理者",
            "教练辅导：一对一指导，深度提升，适合高管"
        ],
        "trainer_categories": [
            "学术型讲师：高校教授，理论基础扎实",
            "实战型讲师：企业高管，经验丰富案例多",
            "咨询型讲师：咨询顾问，方法论体系完善",
            "技能型讲师：专业技术人才，实操能力强",
            "认证型讲师：持专业认证资质，标准化授课"
        ],
        "venue_recommendations": [
            "酒店会议厅：适合30人以上大型培训",
            "企业培训室：适合内部团队集中培训",
            "共享空间：适合小型工作坊灵活预约",
            "度假村/山庄：适合团队建设和封闭培训",
            "线上平台：适合分布式团队远程培训"
        ],
        "evaluation_methods": [
            "反应层评估：学员满意度问卷和反馈",
            "学习层评估：课前课后测试知识掌握度",
            "行为层评估：跟踪学员工作中行为改变",
            "结果层评估：衡量培训对业务指标的影响",
            "ROI评估：计算培训投入产出比"
        ]
    }
}

CAPABILITIES_MANUFACTURING_SAMPLING = {
    "status_machine": {
        "states": [
            {
                "id": "requirement_collection",
                "name": "需求收集",
                "description": "收集代工打样需求信息"
            },
            {
                "id": "factory_matching",
                "name": "工厂匹配",
                "description": "匹配合适的代工厂"
            },
            {
                "id": "sample_development",
                "name": "打样开发",
                "description": "工厂进行样品开发和制作"
            },
            {
                "id": "sample_review",
                "name": "样品审核",
                "description": "审核确认样品质量和规格"
            },
            {
                "id": "mass_production",
                "name": "批量生产",
                "description": "进入批量生产阶段"
            },
            {
                "id": "quality_inspection",
                "name": "质量检验",
                "description": "进行生产过程质量检验"
            },
            {
                "id": "delivery",
                "name": "交货出货",
                "description": "完成生产和出货交付"
            },
            {
                "id": "settlement",
                "name": "费用结算",
                "description": "完成代工费用结算"
            }
        ],
        "transitions": [
            [
                "requirement_collection",
                "factory_matching"
            ],
            [
                "factory_matching",
                "sample_development"
            ],
            [
                "sample_development",
                "sample_review"
            ],
            [
                "sample_review",
                "mass_production"
            ],
            [
                "mass_production",
                "quality_inspection"
            ],
            [
                "quality_inspection",
                "delivery"
            ],
            [
                "delivery",
                "settlement"
            ],
            [
                "sample_review",
                "sample_development"
            ],
            [
                "quality_inspection",
                "mass_production"
            ]
        ]
    },
    "agent_auto": [
        {
            "id": "factory_search",
            "name": "工厂搜索",
            "description": "AI自动搜索和匹配代工厂"
        },
        {
            "id": "capability_analysis",
            "name": "能力分析",
            "description": "AI自动分析工厂生产能力和资质"
        },
        {
            "id": "cost_estimation",
            "name": "成本估算",
            "description": "AI自动估算代工成本"
        },
        {
            "id": "timeline_projection",
            "name": "工期预估",
            "description": "AI自动预估生产周期和排期"
        },
        {
            "id": "material_sourcing_analysis",
            "name": "原料采购分析",
            "description": "AI自动分析原材料采购渠道和价格"
        },
        {
            "id": "quality_standard_matching",
            "name": "质量标准匹配",
            "description": "AI自动匹配行业质量标准要求"
        },
        {
            "id": "progress_tracking",
            "name": "进度跟踪",
            "description": "AI自动跟踪生产进度并更新状态"
        }
    ],
    "human_required": [
        {
            "id": "factory_audit",
            "name": "工厂审核",
            "description": "人工实地审核工厂的生产资质和条件"
        },
        {
            "id": "sample_design_review",
            "name": "样品设计审核",
            "description": "人工审核样品设计稿和技术规格"
        },
        {
            "id": "on_site_inspection",
            "name": "现场检验",
            "description": "人工到工厂进行现场质量检验"
        },
        {
            "id": "production_line_visit",
            "name": "产线考察",
            "description": "人工参观考察生产流水线"
        },
        {
            "id": "acceptance_testing",
            "name": "验收测试",
            "description": "人工进行成品验收测试和确认"
        }
    ],
    "escalation_conditions": [
        {
            "condition": "sample_rejected_3times",
            "description": "样品连续三次打样不合格时升级人工处理"
        },
        {
            "condition": "quality_defect_rate_high",
            "description": "质量不良率超过标准时升级人工处理"
        },
        {
            "condition": "delivery_delay",
            "description": "交货延期可能影响客户交付时升级人工处理"
        },
        {
            "condition": "material_shortage",
            "description": "原材料短缺影响生产排期时升级人工处理"
        },
        {
            "condition": "order_quantity_change",
            "description": "订单数量发生重大变更时升级人工处理"
        }
    ],
    "knowledge_base": {
        "manufacturing_types_by_industry": [
            "OEM代工：按客户设计图纸和规格生产",
            "ODM代工：工厂自主设计开发供客户选择",
            "OBM代工：工厂自有品牌代工生产",
            "EMS代工：电子制造服务，含采购和测试",
            "CMT代工：来料加工，裁切缝制包装"
        ],
        "factory_evaluation_criteria": [
            "资质认证：ISO9001、ISO14001等行业认证",
            "产能规模：月产量、设备数量、工人规模",
            "质量管理：质检流程、不良率、客诉率",
            "交期表现：准时交付率、紧急订单响应",
            "价格竞争力：报价水平、价格透明度",
            "研发能力：设计团队、打样速度、创新能力"
        ],
        "sampling_process_explanation": [
            "初步打样：根据设计图制作首版样品",
            "修改打样：根据反馈意见修改样品",
            "确认样：客户确认签样的最终版本",
            "封样：留存标准样品作为量产依据",
            "产前样：量产前小批量试产样品验证"
        ],
        "quality_standards_by_industry": [
            "电子行业：IPC-A-610焊接标准，ESD防静电",
            "纺织服装：AQL2.5/4.0抽检标准，色牢度测试",
            "食品行业：HACCP认证，微生物检测标准",
            "玩具行业：EN71(欧盟)、ASTM F963(美国)",
            "汽车零部件：IATF 16949质量体系标准"
        ]
    }
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
        "description": "企业团队建设活动策划与执行。户外拓展、室内团建、主题工作坊、竞技游戏等。AI根据团队人数、预算、偏好推荐最优方案，一站搞定方案设计、供应商匹配、预订执行和现场协调。",
        "status": "live",
        "schema_model": TeamBuildingParams,
        "estimated_days": "3-7",
        "price_range": "按方案报价",
        "required_documents": [
            "企业基本信息（名称、联系人）",
            "团队人数和人员构成说明",
            "活动预算（人均或总预算）",
            "活动偏好和时间要求",
            "特殊需求说明（如有）",
        ],
        "capabilities": CAPABILITIES_TEAM_BUILDING,
        "workflow_steps": [
            {"step_id": "requirement_collection", "name": "需求收集", "order": 1, "agent_auto": True},
            {"step_id": "scheme_design", "name": "方案设计", "order": 2, "agent_auto": True},
            {"step_id": "scheme_confirmation", "name": "方案确认", "order": 3, "agent_auto": True},
            {"step_id": "supplier_matching", "name": "供应商匹配", "order": 4, "agent_auto": False},
            {"step_id": "booking", "name": "预订执行", "order": 5, "agent_auto": False},
            {"step_id": "preparation", "name": "筹备阶段", "order": 6, "agent_auto": False},
            {"step_id": "execution", "name": "活动执行", "order": 7, "agent_auto": False, "human_role": "现场协调员"},
            {"step_id": "settlement", "name": "结算确认", "order": 8, "agent_auto": True},
        ],
    },
    "business_dining": {
        "name": "商务宴请",
        "description": "商务宴请一站式安排。餐厅推荐、菜单定制、包间预订、酒水搭配、礼品准备。AI根据接待规格、预算、口味偏好推荐，从订餐到接待全程保障。",
        "status": "live",
        "schema_model": BusinessDiningParams,
        "estimated_days": "1-3",
        "price_range": "免费咨询",
        "required_documents": [
            "企业名称和联系人信息",
            "用餐人数和宾客说明",
            "宴请目的和接待规格",
            "预算（人均或总预算）",
            "菜系偏好和饮食禁忌",
            "开票信息（如需报销）",
        ],
        "capabilities": CAPABILITIES_BUSINESS_DINING,
        "workflow_steps": [
            {"step_id": "requirement_collection", "name": "需求收集", "order": 1, "agent_auto": True},
            {"step_id": "restaurant_recommendation", "name": "餐厅推荐", "order": 2, "agent_auto": True},
            {"step_id": "menu_design", "name": "菜单定制", "order": 3, "agent_auto": False, "human_role": "餐饮顾问"},
            {"step_id": "reservation", "name": "预订确认", "order": 4, "agent_auto": False},
            {"step_id": "special_arrangement", "name": "特殊安排", "order": 5, "agent_auto": False},
            {"step_id": "execution", "name": "宴请执行", "order": 6, "agent_auto": False, "human_role": "现场接待员"},
            {"step_id": "settlement", "name": "结算反馈", "order": 7, "agent_auto": True},
        ],
    },
    "corporate_procurement": {
        "name": "企业采购",
        "description": "企业办公用品、设备、礼品等采购。比价后报价，透明中间价。AI根据需求自动比价推荐最优供应商。",
        "status": "live",
        "schema_model": CorporateProcurementParams,
        "estimated_days": "2-5",
        "price_range": "按需报价",
        "capabilities": CAPABILITIES_CORPORATE_PROCUREMENT,
        "workflow_steps": [
            {"step_id": "requirement_collection", "name": "需求收集", "order": 1, "agent_auto": True},
            {"step_id": "supplier_matching", "name": "供应商匹配", "order": 2, "agent_auto": True},
            {"step_id": "quotation_comparison", "name": "报价对比", "order": 3, "agent_auto": True},
            {"step_id": "negotiation", "name": "商务谈判", "order": 4, "agent_auto": False, "human_role": "采购专员"},
            {"step_id": "order_confirmation", "name": "订单确认", "order": 5, "agent_auto": False},
            {"step_id": "delivery_tracking", "name": "物流跟踪", "order": 6, "agent_auto": True},
            {"step_id": "acceptance_check", "name": "验收检查", "order": 7, "agent_auto": False, "human_role": "质检员"},
            {"step_id": "settlement", "name": "结算付款", "order": 8, "agent_auto": False},
        ],
    },
    "logistics_delivery": {
        "name": "物流配送",
        "description": "企业物流配送服务。文件、包裹、货物等。对接多家运力，选最优方案。",
        "status": "live",
        "schema_model": LogisticsDeliveryParams,
        "estimated_days": "1-3",
        "price_range": "比价报价",
        "capabilities": CAPABILITIES_LOGISTICS_DELIVERY,
        "workflow_steps": [
            {"step_id": "requirement_collection", "name": "需求收集", "order": 1, "agent_auto": True},
            {"step_id": "carrier_matching", "name": "承运商匹配", "order": 2, "agent_auto": True},
            {"step_id": "booking", "name": "预约下单", "order": 3, "agent_auto": True},
            {"step_id": "pickup", "name": "上门取件", "order": 4, "agent_auto": False},
            {"step_id": "in_transit", "name": "运输中", "order": 5, "agent_auto": True},
            {"step_id": "delivery", "name": "派送中", "order": 6, "agent_auto": False},
            {"step_id": "confirmation", "name": "签收确认", "order": 7, "agent_auto": True},
            {"step_id": "settlement", "name": "费用结算", "order": 8, "agent_auto": True},
        ],
    },
    "sales_outsourcing": {
        "name": "销售外包",
        "description": "企业销售业务外包服务。电销、地推、渠道拓展等。按效果付费，免费需求匹配。",
        "status": "live",
        "schema_model": SalesOutsourcingParams,
        "estimated_days": "视项目而定",
        "price_range": "按效果付费",
        "capabilities": CAPABILITIES_SALES_OUTSOURCING,
        "workflow_steps": [
            {"step_id": "requirement_collection", "name": "需求收集", "order": 1, "agent_auto": True},
            {"step_id": "team_matching", "name": "团队匹配", "order": 2, "agent_auto": True},
            {"step_id": "contract_signing", "name": "合同签署", "order": 3, "agent_auto": False},
            {"step_id": "team_onboarding", "name": "团队入职", "order": 4, "agent_auto": False, "human_role": "培训师"},
            {"step_id": "execution", "name": "执行阶段", "order": 5, "agent_auto": False},
            {"step_id": "reporting", "name": "报告汇报", "order": 6, "agent_auto": True},
            {"step_id": "performance_review", "name": "绩效评估", "order": 7, "agent_auto": True},
            {"step_id": "settlement", "name": "结算付款", "order": 8, "agent_auto": True},
        ],
    },
    "third_party_operations": {
        "name": "代运营",
        "description": "企业新媒体/电商平台代运营。抖音、小红书、淘宝、京东等。免费方案推荐。",
        "status": "live",
        "schema_model": EcommerceOperationsParams,
        "estimated_days": "月度服务",
        "price_range": "3000-20000/月",
        "capabilities": CAPABILITIES_ECOMMERCE_OPERATIONS,
        "workflow_steps": [
            {"step_id": "requirement_collection", "name": "需求收集", "order": 1, "agent_auto": True},
            {"step_id": "platform_analysis", "name": "平台分析", "order": 2, "agent_auto": True},
            {"step_id": "strategy_design", "name": "策略设计", "order": 3, "agent_auto": True},
            {"step_id": "contract_signing", "name": "合同签署", "order": 4, "agent_auto": False},
            {"step_id": "team_setup", "name": "团队组建", "order": 5, "agent_auto": False},
            {"step_id": "content_creation", "name": "内容制作", "order": 6, "agent_auto": False, "human_role": "运营专员"},
            {"step_id": "operation_execution", "name": "运营执行", "order": 7, "agent_auto": True},
            {"step_id": "data_reporting", "name": "数据报告", "order": 8, "agent_auto": True},
            {"step_id": "settlement", "name": "结算付款", "order": 9, "agent_auto": True},
        ],
    },
    "recruitment_outsourcing": {
        "name": "猎头/招聘外包",
        "description": "企业招聘外包服务。高端猎头、批量招聘、RPO。按结果收费。",
        "status": "live",
        "schema_model": RecruitmentOutsourcingParams,
        "estimated_days": "视职位而定",
        "price_range": "年薪15-25%",
        "capabilities": CAPABILITIES_RECRUITMENT_OUTSOURCING,
        "workflow_steps": [
            {"step_id": "requirement_collection", "name": "需求收集", "order": 1, "agent_auto": True},
            {"step_id": "position_analysis", "name": "职位分析", "order": 2, "agent_auto": True},
            {"step_id": "candidate_search", "name": "候选人搜索", "order": 3, "agent_auto": True},
            {"step_id": "screening", "name": "简历筛选", "order": 4, "agent_auto": True},
            {"step_id": "interview_arrangement", "name": "面试安排", "order": 5, "agent_auto": True},
            {"step_id": "offer_management", "name": "Offer管理", "order": 6, "agent_auto": False, "human_role": "猎头顾问"},
            {"step_id": "onboarding", "name": "入职跟进", "order": 7, "agent_auto": False},
            {"step_id": "probation_review", "name": "试用期评估", "order": 8, "agent_auto": True},
            {"step_id": "settlement", "name": "费用结算", "order": 9, "agent_auto": True},
        ],
    },
    "corporate_training": {
        "name": "企业培训",
        "description": "企业内训服务。管理培训、技能培训、团建培训等。免费比价，推荐最优讲师。",
        "status": "live",
        "schema_model": CorporateTrainingParams,
        "estimated_days": "按场次",
        "price_range": "5000-50000/场",
        "capabilities": CAPABILITIES_CORPORATE_TRAINING,
        "workflow_steps": [
            {"step_id": "requirement_collection", "name": "需求收集", "order": 1, "agent_auto": True},
            {"step_id": "needs_assessment", "name": "需求调研", "order": 2, "agent_auto": True},
            {"step_id": "trainer_matching", "name": "讲师匹配", "order": 3, "agent_auto": True},
            {"step_id": "program_design", "name": "方案设计", "order": 4, "agent_auto": True},
            {"step_id": "contract_signing", "name": "合同签署", "order": 5, "agent_auto": False},
            {"step_id": "training_execution", "name": "培训执行", "order": 6, "agent_auto": False, "human_role": "讲师"},
            {"step_id": "evaluation", "name": "评估反馈", "order": 7, "agent_auto": True},
            {"step_id": "settlement", "name": "结算付款", "order": 8, "agent_auto": True},
        ],
    },
    "manufacturing_sampling": {
        "name": "代工打样",
        "description": "工厂代工/打样/小批量生产。免费工厂匹配，按量报价。覆盖电子、服装、五金、塑料等行业。",
        "status": "live",
        "schema_model": ManufacturingSamplingParams,
        "estimated_days": "视产品而定",
        "price_range": "按量报价",
        "capabilities": CAPABILITIES_MANUFACTURING_SAMPLING,
        "workflow_steps": [
            {"step_id": "requirement_collection", "name": "需求收集", "order": 1, "agent_auto": True},
            {"step_id": "factory_matching", "name": "工厂匹配", "order": 2, "agent_auto": True},
            {"step_id": "sample_development", "name": "打样开发", "order": 3, "agent_auto": False, "human_role": "工厂技术员"},
            {"step_id": "sample_review", "name": "样品审核", "order": 4, "agent_auto": False},
            {"step_id": "mass_production", "name": "批量生产", "order": 5, "agent_auto": False},
            {"step_id": "quality_inspection", "name": "质量检验", "order": 6, "agent_auto": False, "human_role": "质检员"},
            {"step_id": "delivery", "name": "交货发运", "order": 7, "agent_auto": True},
            {"step_id": "settlement", "name": "结算付款", "order": 8, "agent_auto": True},
        ],
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
