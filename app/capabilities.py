

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
