# Human Gates 项目全貌梳理

## 从零到 v0.3.0 的完整生命周期

---

## 一、项目起源与核心洞察

### 1.1 起源

Human Gates 的诞生源于创始人的一个核心洞察：

**注册公司最大的成本不是工本费，是资料来回修改、信息反复确认的沟通成本。**

创始人（尹宁西 / Nassen Yin）想做一人公司（技术创业）全生命周期服务的 API 平台。他所在的公司是"中海冀交（河北）绿色能源科技有限公司"，担任党群宣传岗，但同时也是一位技术创业者。

### 1.2 产品定位的三次演变

| 阶段 | 定位 | 描述 |
|------|------|------|
| 初期 | API 聚合平台 | 聚合各类代办服务商，提供统一 API 入口 |
| 中期 | 工单系统 | 标准化提交 -> 人工处理的流程引擎 |
| 最终（自定） | **纯协议层** | 消除人与人之间的沟通成本 |

最终自定的定位最为关键。Human Gates 只做四件事：
- Schema 定义（数据结构标准化）
- Validation（字段校验、交叉校验）
- 状态机（业务流程编排）
- 路由编排（匹配服务商/第三方）

**核心价值主张**：让 AI 一次读全、一次填对，省掉反复沟通的流程。

物理活（递交/跑腿/签字）外包给 e签宝或人工代办。Human Gates 不做执行层，只做协议层。

### 1.3 产品名称与域名

- 产品名：Human Gates（复数，代表多个服务门）
- 域名：humangates.com（已在阿里云万网注册）
- GitHub：github.com/nassen-yin/humangates

### 1.4 竞品研究

| 竞品 | 市场 | 定位 |
|------|------|------|
| Human API ($65M) | Western | 同类平台 |
| Rentahuman.ai (Feb 2026) | Western | 同类平台 |
| Human Gates | 中国 | 市场空白，暂无直接竞品 |

中国市场同类产品空白，是项目的主要机会点。

---

## 二、技术架构总览

### 2.1 技术栈

| 层 | 技术选型 |
|---|----------|
| 框架 | Python FastAPI |
| 数据库 | SQLite（MVP 阶段） |
| 认证 | API Key 双体系（Master + Admin） |
| 开发环境 | macOS 本地 |
| 部署目标 | 阿里云轻量服务器（尚未部署） |
| 通知渠道 | WeChat 网关（端口 8642） |

### 2.2 项目结构

```
human-gates/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI 入口 + 根页面 + 路由注册
│   ├── config.py          # 配置（版本、API Key、前缀）
│   ├── database.py        # SQLite 数据库初始化 + 连接
│   ├── models.py          # Pydantic 数据模型 + 服务注册表 + 状态机
│   ├── auth.py            # API Key 认证中间件
│   └── routers/
│       ├── __init__.py
│       ├── tasks.py       # 任务 CRUD + 状态流转 + 时间线
│       ├── services.py    # 服务目录 API（AI 的第一个问题）
│       ├── files.py       # 文件上传/查看
│       └── operations.py  # 进度查询、文书管理、审计日志
├── www/
│   ├── index.html         # 首页 — 品牌定位页
│   ├── api-docs.html      # API 文档（14 个章节）
│   ├── pricing.html       # 价格页面
│   ├── css/style.css      # 飞书蓝色主题样式（895 行）
│   └── js/main.js         # 前端交互脚本
├── cli.py                 # 命令行管理工具
├── humangates.db          # SQLite 数据库文件
├── uploads/               # 上传文件存储目录
├── market_data.py         # 无关脚本（郑商所期货行情工具）
├── README.md              # 项目说明（v0.2.0 版本）
├── UPGRADE.md             # v0.2.0 升级计划
├── requirements.txt       # 依赖：fastapi, uvicorn, pydantic, pydantic-settings, python-dotenv
├── .env                   # API Key 配置
└── .env.example           # 环境变量模板
```

### 2.3 当前架构模式

```
客户 AI Agent
    |
    v
Human Gates API（协议层 + 校验 + 智能预处理）
    |
    v
e签宝 API（外部服务层：实名认证 -> 电子签名 -> 递交工商局）
    |
    v
工商局（物理世界终点）
```

### 2.4 API 密钥

- MASTER_API_KEY（开发者调用，查看+创建任务）
- ADMIN_API_KEY（管理员调用，更新状态+上传文件+生成文书）

---

## 三、完整版本演变

### 3.1 v0.1.0 — MVP 初始版本

**Git 提交**：d5c13a6 "chore: initial MVP"（2026-05-08，仅此一个提交）
**GitHub**：已推送（后续版本未推）

#### 功能
- 基础 CRUD API：创建、查询、列表、更新
- 8 字段公司注册模型（简单参数）
- 6 状态状态机：pending_review / needs_info / materials_ready / in_progress / completed / failed
- CLI 管理工具
- 文件上传基础功能

#### 初始文件（14 个）
- .env.example, .gitignore, README.md, requirements.txt
- app/__init__.py, app/auth.py, app/config.py, app/database.py, app/main.py, app/models.py
- app/routers/__init__.py, app/routers/tasks.py
- cli.py, tests/__init__.py

#### 初始 models.py — 仅 34 行
只有最基础的 TaskCreate、TaskUpdate 模型，无服务目录，无复杂校验。

### 3.2 v0.2.0 — 服务目录 + 结构化参数

**说明**：未单独提交 Git，代码直接演进到当前状态。

#### 新增功能
1. **服务目录概念**：GET /v1/services — AI 调用后决定要什么服务
2. **6 个服务品类**：
   - 公司注册（live）— 已上线
   - 代理记账（coming_soon）— Schema 就绪
   - 税务登记（planning）
   - 银行开户（planning）
   - 资质代办（planning）
   - 工商变更（planning）
3. **公司注册扩展**：从 8 个字段扩展到 18 个顶层字段 + 12 个子字段
   - Shareholder 模型：姓名、身份证号、手机号、出资额、比例、职务、地址等
   - Executive 模型：高管任职信息
   - RegisteredAddress 模型：地址类型、详细地址、产权信息、租赁信息
   - ArticlesOfAssociation 模型：利润分配、表决权、法定代表人产生方式等
   - BusinessScope 模型：行业代码、经营项目、前置许可
4. **状态机修复**：in_progress -> needs_info 被允许
5. **新增路由**：services.py（服务目录）、files.py（文件上传/查看）
6. **数据库新增表**：files、task_logs
7. **网站三页全部重写**：品牌定位为"打通 AI 与人类世界的最后一公里"

#### 关键文件变更
- UPGRADE.md 记录了完整的 v0.2.0 升级计划
- models.py 从 34 行大幅扩展
- 新增 app/routers/services.py 和 app/routers/files.py
- database.py 从 1 张表扩展到 3 张表

### 3.3 v0.2.1 — 服务目录增强

#### 新增功能
1. **GET /v1/services 成为 AI 的第一个问题**
   - AI Agent 必须先查询服务目录，再提交任务
   - 返回完整 JSON Schema 供 AI 理解数据结构
2. **代理记账 Schema 就绪**：12 个字段定义完毕（company_name, taxpayer_type, monthly_invoice_count 等）
3. **网站更新**：
   - 首页新增"服务蓝图"板块，展示所有品类及状态
   - API 文档新增"服务目录"章节

### 3.4 v0.3.0 — 当前最新版本（能力体系 + e签宝集成）

**版本标签**：index.html 中标注为 "v0.2.0"（网站尚未更新版本号），但代码已是 v0.3.0 完整实现。
**GitHub**：尚未推送。

#### 核心新增

##### A. 8 状态状态机

```
draft -> materials_collecting -> name_verification -> submitting -> in_progress -> approved -> completed
    |           |                    |                    |               |
    +---------> needs_info <---------+--------------------+---------------+
                                                                        -> failed
```

| 状态 | 含义 |
|------|------|
| draft | 初始状态，信息不完整 |
| materials_collecting | 材料收集阶段 |
| name_verification | 名称核准中 |
| submitting | 已提交至工商局 |
| in_progress | 工商局审核中 |
| needs_info | 需要补充材料（可从任何活跃状态进入） |
| approved | 审核通过 |
| completed | 已完成（执照已领取） |
| failed | 任务失败（终态） |

##### B. Capabilities 能力体系

**agent_auto（10 项 AI 可独立完成）**：
1. 格式校验 — 身份证号、手机号、注册资本等字段格式
2. 交叉校验 — 出资额求和=注册资本、法人不得兼任监事
3. 条件必填判断 — 根据已有字段值判断哪些字段需补充
4. 文件基础检查 — 文件类型、大小、OCR 可读性
5. 文书自动生成 — 从字段填充模板生成全套文书
6. 文书一致性校验 — 检查所有文件中公司名、股东名、金额一致性
7. 状态流转 — 根据状态机自动推进或退回
8. 名称预检 — 检查名称格式、禁限词、长度
9. 名称驳回自动处理 — 工商局驳回时自动生成替代方案
10. 经营范围自动转化 — 口头业务描述映射为工商标准表述

**human_required（7 项需要真人介入）**：
1. 工商局递交 — 需要 CA 证书/电子营业执照签名
2. 驳回原因解读 — 自由裁量需要人工判断补件策略
3. 电话核实 — 工商局/税务来电需真人接听
4. 签字/盖章 — 法律文件需亲笔签字或公章
5. 异常流程处理 — 税务登记卡住、地址抽查等
6. 线下跑腿 — 某些城市必须线下递交材料
7. 进度催办 — 超时未办结需真人电话/现场催办

**escalation（5 个转人条件）**：
1. 工商局返回非结构化驳回 -> 标记 needs_info
2. 名称知识库无匹配 -> 生成 3 个替代名称 + 转人工
3. 前置许可需要确认 -> 标记待人工审核
4. 线下递交要求 -> 输出准备清单 + 通知人工
5. 超时未推进 -> 标记催办 + 通知人工

##### C. 名称驳回知识库（6 条全国通用规则）

| 模式 | 建议 |
|------|------|
| 重名/已存在/已被注册 | 更换字号或加行业限定词 |
| 近似/相似/容易混淆 | 加地域修饰词，或改三个字字号 |
| 驰名商标/知名品牌 | 完全避免使用相同字词 |
| 敏感/禁限词 | 去除禁限词，特批转人工 |
| 行业表述不规范 | 参照《国民经济行业分类》调整 |
| 字号与行业不匹配 | 体现行业特征或明确行业限定词 |

匹配成功自动生成 3 个替代名称，无匹配则转人工。

##### D. 经营范围映射表（20 组关键词）

覆盖软件开发、电商、网站设计、教育培训、平面设计、新媒体、外贸、咨询、餐饮、建筑、物流、广告、贸易、医疗、农业、酒店、会展、知识产权、人力资源等。

自动填充率约 80%（fully_matched），部分匹配 15%，无匹配 5% 转人工。

##### E. 城市分级 + e签宝集成

**城市分级**：
- 第一梯队（5 城）：北京、上海、广州、深圳、杭州 — e签宝已覆盖，零人工
- 第二梯队（7 城）：成都、南京、武汉、重庆、天津、苏州、宁波 — 待验证
- 其他城市：暂不支持，转人工代办

**e签宝集成**：
- 价格：SaaS API 标准版 8 元/份
- 5 个 API 端点：实名认证、企业认证、签署流程创建、签署执行、工商注册提交
- 6 步工作流：
  1. Human Gates 完成预处理
  2. -> e签宝实名认证 -> 人脸识别
  3. -> e签宝企业认证 -> 电子印章
  4. -> 发起签署 -> 股东在线签名
  5. -> 提交至工商局
  6. -> 接收回调 -> 获取电子营业执照

##### F. 新增 5 个 Endpoint

| 端点 | 方法 | 功能 |
|------|------|------|
| /v1/tasks/{id}/progress | GET | 11 步流程分解，每步百分比 |
| /v1/tasks/{id}/documents | GET | 查看已生成的文书列表及状态 |
| /v1/tasks/{id}/audit-log | GET | 完整操作审计日志 |
| /v1/tasks/{id}/documents | POST | 文书生成（4 类：章程、股东会决议、任职文件、租赁合同） |

##### G. 数据库新增表
- documents — 文书记录（类型、状态、文件路径）
- document_generation_queue — 文书生成队列

##### H. JSON Schema x-validation 注入规则
- 身份证号：18 位格式 + 校验位算法
- 手机号：11 位格式
- 公司名称：汉字+有限公司格式、禁限词检查
- 注册资本：整数校验

##### I. 11 步工作流（公司注册完整流程分解）

| 步骤 | 名称 | 是否 AI 自动 |
|------|------|:------:|
| 1 | name_verification | 名称核准 | Yes |
| 2 | shareholder_info | 股东信息 | Yes |
| 3 | legal_representative | 法定代表人信息 | Yes |
| 4 | registered_capital | 注册资本 | Yes |
| 5 | registered_address | 注册地址 | Yes |
| 6 | business_scope | 经营范围 | Yes |
| 7 | articles_of_association | 公司章程 | Yes |
| 8 | document_generation | 文书生成 | Yes |
| 9 | e_sign_submission | e签宝递交 | No（外部） |
| 10 | governance_review | 工商局审核 | No |
| 11 | license_collection | 执照领取 | No |

---

## 四、API 文档完整章节（v0.3.0 网站，14 个章节）

1. 概述 — 什么是 Human Gates
2. 设计理念 — 纯协议层，消除沟通成本
3. 服务目录 — GET /v1/services
4. 认证 — X-API-Key / X-Admin-Key
5. 创建任务 — POST /v1/tasks
6. 查询列表 — GET /v1/tasks
7. 查询详情 — GET /v1/tasks/{id}
8. 更新状态 — PUT /v1/tasks/{id}/status
9. 进度查询 — GET /v1/tasks/{id}/progress（v0.3 新增）
10. 文档生成 — POST /v1/tasks/{id}/documents（v0.3 新增）
11. 文书列表 — GET /v1/tasks/{id}/documents（v0.3 新增）
12. 文件上传 — POST /v1/tasks/{id}/files
13. 时间线 — GET /v1/tasks/{id}/timeline
14. 审计日志 — GET /v1/tasks/{id}/audit-log（v0.3 新增）
15. 数据模型 — 全部 Pydantic Schema

---

## 五、商业模式与定价

### 定价策略
- API 调用免费，执行成功才收费
- 公司注册：699-1299 元（含核名 + 营业执照 + 刻章）
- 代理记账：200 元/月（小规模纳税人）
- 其他品类按需定价

### 计费原则
- 服务费含：资料审核、服务商匹配、进度跟踪、结果回传
- 不包含政府规费（刻章费、工本费），实报实销
- 因政策变动或不可抗力导致无法办理，全额退款
- 因资料造假导致驳回，酌情扣除审核成本

### 商业模式（平台模式）

```
AI Agent / 开发者 -> Human Gates API -> 运营中心 -> 服务商网络 -> 物理世界完成
```

Human Gates 不直接雇人跑腿，而是通过服务商网络（注册制）完成物理交付。

---

## 六、开发者生态规划

### 已实现
- REST API（全部 v1 端点）
- CLI 命令行管理工具
- 网站三页（首页/API 文档/价格）

### 规划中（Q3 2026）
- Supplier 客户端（服务商入驻、派单、结算系统）
- GitHub SDK（各语言开发者工具包）
- MCP Server（Model Context Protocol 服务器）
- Webhook 回调机制

### 定位策略
- 走开发者生态（GitHub SDK, MCP Server）
- 不做 SEO/GEO 获客

---

## 七、核心设计决策记录

1. **"API 调用仅限 AI"** — 接口设计面向 AI Agent 而非人类 UI。让对方 AI 读懂了 API 后引导用户将各个步骤标准化完成，省掉人与人之间的沟通成本。

2. **"甩个链接让他们一注册"** — 服务商入驻模式。不需要复杂签约，一个链接完成入驻审核，谁干不是干。

3. **不做执行层，做协议层** — Human Gates 只做 Schema definition、Validation、State machine、Routing。物理活外包给 e签宝或人工代办。

4. **先石家庄公司注册，再扩展到全国** — MVP 聚焦一个城市一个品类，验证模式后再横向扩展。

5. **第一梯队优先 e签宝** — 5 个一线/新一线城市全程线上，通过 e签宝 API 完成而没有人工介入。

6. **能力体系分层设计** — agent_auto / human_required / escalation 三层，清晰界定 AI 能做和不能做的边界，是 v0.3 最核心的架构升级。

---

## 八、剩余工作（To Do）

### 短期（当前待完成）
1. 推 v0.3.0 到 GitHub（当前 v0.2.1 + v0.3.0 代码均未推）
2. 更新网站版本号（index.html 仍显示 v0.2.0）
3. 部署到阿里云轻量服务器
4. 配置 humangates.com DNS 解析

### 中期
5. 更多品类 Schema 开发（银行开户、税务登记、资质代办、工商变更）
6. Supplier 客户端开发（Q3 2026）

### 长期
7. 开发者 SDK / MCP Server
8. 更多城市覆盖（第二梯队验证后开放）

---

## 九、关键文件清单（v0.3.0 最终状态）

| 文件 | 作用 | 行数 |
|------|------|:----:|
| app/models.py | 核心：服务注册表 + 8 状态机 + capabilities + Schema | 634 |
| app/main.py | FastAPI 入口 + 路由注册 | 47 |
| app/database.py | SQLite 初始化（5 张表）+ 连接 | 97 |
| app/config.py | 配置管理 | 22 |
| app/auth.py | API Key 双体系认证 | 24 |
| app/routers/tasks.py | 任务 CRUD + 状态机 + 时间线 | 183 |
| app/routers/services.py | 服务目录 API | 51 |
| app/routers/files.py | 文件上传/查看 | 101 |
| app/routers/operations.py | 进度/文书/审计日志（v0.3 新增） | 263 |
| www/index.html | 首页 — 品牌定位 | 285 |
| www/api-docs.html | API 文档（14 章） | 558 |
| www/pricing.html | 价格页 | 234 |
| www/css/style.css | 飞书蓝色主题 | 895 |
| cli.py | 命令行管理工具 | 245 |
| README.md | 项目说明（v0.2.0） | 136 |
| UPGRADE.md | v0.2.0 升级计划 | 40 |

---

*文档生成日期：2026-05-12*
*基于代码仓库：/Users/yinningxi/human-gates（Git 仅 1 个 commit）*
*基于会话上下文：多轮微信同步 + 代码审查*
