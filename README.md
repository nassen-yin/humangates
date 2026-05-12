# Human Gates

**AI agent 的物理世界任务交付层。**

AI agent 在数字世界能做几乎一切事——但卡在需要真人的最后一步：
公司注册要人去工商局、银行开户要法人面签、资质办理要提交纸质材料。

Human Gates 填补这个缺口：**API 接单 → 人工审核 → 派单给本地服务商 → 真人执行 → 结果回传。**

## v0.2.0 新功能

- **结构化任务参数** — 公司注册有完整的 schema 校验：股东信息、经营范围、出资比例... 缺了直接报错
- **状态机** — 不再是简单的 pending/completed，而是完整的业务流：pending_review → needs_info → materials_ready → in_progress → completed/failed
- **文件上传** — 身份证照片、地址证明等材料可以上传并关联到任务
- **时间线** — 每一步状态变更都有记录，含备注
- **备注/沟通** — 可以在任务上添加备注，用于客服/服务商沟通

## 快速开始

```bash
# 安装
pip install -r requirements.txt

# 配置
cp .env.example .env
# 编辑 .env，设置 MASTER_API_KEY 和 ADMIN_API_KEY

# 启动
uvicorn app.main:app --reload --port 8000

# 访问
# API: http://localhost:8000/v1/tasks
# 文档: http://localhost:8000/docs
```

## API 使用

```bash
# 创建公司注册任务
curl -X POST http://localhost:8000/v1/tasks \
  -H "X-API-Key: your-master-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "company_registration",
    "params": {
      "company_names": ["示例科技有限公司"],
      "business_scope": "软件开发；信息技术咨询",
      "registered_capital": 100,
      "shareholders": [
        {"name": "张三", "id_number": "130123...", "phone": "138...",
         "capital_contribution": 60, "percentage": 60, "role": "legal_person"},
        {"name": "李四", "id_number": "130123...", "phone": "139...",
         "capital_contribution": 40, "percentage": 40, "role": "supervisor"}
      ],
      "address_type": "lease",
      "address_detail": "河北省石家庄市长安区中山路100号",
      "contact_name": "张三",
      "contact_phone": "13800138000"
    }
  }'

# 查看任务时间线
curl http://localhost:8000/v1/tasks/{task_id}/timeline \
  -H "X-API-Key: your-master-api-key"

# 添加备注（管理员）
curl -X POST http://localhost:8000/v1/tasks/{task_id}/notes \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"note": "客户要求加急"}'

# 上传文件（管理员）
curl -X POST http://localhost:8000/v1/tasks/{task_id}/files \
  -H "X-Admin-Key: your-admin-key" \
  -F "file=@id_card.jpg" \
  -F "file_type=id_card_front"

# 更新任务状态（管理员）
curl -X PUT http://localhost:8000/v1/tasks/{task_id}/status \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "note": "执照已领取",
    "result": {"license_number": "91130100MAXXXX"}
  }'
```

## 状态机

```
pending_review ──→ needs_info ──→ pending_review
       │                │
       └──→ materials_ready ──→ in_progress ──→ completed
                │                     │
                └──→ failed ←─────────┘
```

每个状态都有明确的可转换目标，非法转换会被拒绝。

## CLI 管理工具

```bash
python3 cli.py list                          # 查看所有任务
python3 cli.py list --status pending_review  # 只看待审核的
python3 cli.py show <task_id>                # 查看详情（含文件和时间线）
python3 cli.py timeline <task_id>            # 查看完整时间线
python3 cli.py note <task_id> "补充说明"     # 添加备注
python3 cli.py update <task_id> in_progress --note "已联系服务商"
python3 cli.py update <task_id> completed --result '{"license":"xxxx"}' --note "完成"
python3 cli.py files <task_id>              # 查看上传的文件
```

## 项目结构

```
human-gates/
├── app/
│   ├── main.py         # FastAPI 入口 + 根页面
│   ├── config.py       # 配置
│   ├── database.py     # SQLite（含 files + task_logs 表）
│   ├── models.py       # 数据模型 + schema 校验
│   ├── auth.py         # API Key 认证
│   └── routers/
│       ├── tasks.py    # 任务 CRUD + 状态机 + 时间线
│       └── files.py    # 文件上传/查看
├── cli.py              # 命令行管理工具
├── humangates.db       # SQLite 数据库
├── uploads/            # 上传文件存储
├── requirements.txt
└── .env.example
```

## License

MIT
