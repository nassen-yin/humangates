# Human Gates

**AI agent 的物理世界任务交付层。**

AI agent 在数字世界能做几乎一切事——但卡在需要真人的最后一步：
公司注册要人去工商局、银行开户要法人面签、资质办理要提交纸质材料。

Human Gates 填补这个缺口：API 接单 → 我们核实并安排本地服务商 → 真人执行 → 结果回传。

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
# 创建任务
curl -X POST http://localhost:8000/v1/tasks \
  -H "X-API-Key: your-master-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "company_registration",
    "params": {
      "city": "石家庄",
      "company_name": "示例科技有限公司",
      "founder_name": "张三"
    }
  }'

# 查询任务
curl http://localhost:8000/v1/tasks/{task_id} \
  -H "X-API-Key: your-master-api-key"

# 更新任务状态（管理员用）
curl -X PUT http://localhost:8000/v1/tasks/{task_id}/status \
  -H "X-Admin-Key: your-admin-api-key" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "result": {"license_number": "91130100MAXXXX"}}'
```

## CLI 管理工具

```bash
# 查看任务列表
python cli.py list

# 查看单个任务详情
python cli.py show <task_id>

# 更新任务状态
python cli.py update <task_id> completed --result '{"note": "已办结"}'
```

## 项目结构

```
human-gates/
├── app/
│   ├── main.py        # FastAPI 入口
│   ├── config.py      # 配置
│   ├── database.py    # SQLite 数据库
│   ├── models.py      # 数据模型
│   ├── auth.py        # API Key 认证
│   └── routers/
│       └── tasks.py   # 任务 CRUD 接口
├── cli.py             # 命令行管理工具
├── requirements.txt
└── .env.example
```

## 当前状态

MVP v0.1.0 — 核心 API 已就绪，支持：
- [x] POST /v1/tasks 创建任务
- [x] GET /v1/tasks 查询任务列表
- [x] GET /v1/tasks/{id} 查询单个任务
- [x] PUT /v1/tasks/{id}/status 更新状态
- [x] API Key 认证
- [x] Swagger 文档
- [x] CLI 管理工具

## License

MIT
