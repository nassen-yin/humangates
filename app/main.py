from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from app.config import get_settings
from app.database import init_db
from app.routers import tasks

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Human Gates API — AI agent 的物理世界任务交付层",
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def root():
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Human Gates API</title>
    <style>
        body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;max-width:720px;margin:80px auto;padding:0 24px;line-height:1.7;color:#1a1a1a}
        h1{font-size:2.2rem;margin-bottom:8px}
        h2{font-size:1.3rem;margin-top:40px;color:#555}
        code{background:#f4f4f4;padding:2px 8px;border-radius:4px;font-size:0.9rem}
        pre{background:#f4f4f4;padding:16px;border-radius:8px;overflow-x:auto}
        .endpoint{margin:12px 0;padding:12px 16px;background:#fafafa;border-left:4px solid #2563eb;border-radius:4px}
        .method{display:inline-block;font-weight:700;color:#2563eb;width:60px}
        a{color:#2563eb;text-decoration:none}
        a:hover{text-decoration:underline}
        .footer{margin-top:60px;font-size:0.85rem;color:#888}
    </style>
</head>
<body>
    <h1>Human Gates API</h1>
    <p>AI agent 调用的物理世界任务交付层。<br>
    发一个任务，我们安排真人去执行，结果回传给你。</p>

    <h2>API 端点</h2>

    <div class="endpoint">
        <span class="method">POST</span> <code>/v1/tasks</code>
        <span style="margin-left:12px;color:#666">创建新任务</span>
    </div>
    <div class="endpoint">
        <span class="method">GET</span> <code>/v1/tasks</code>
        <span style="margin-left:12px;color:#666">获取任务列表</span>
    </div>
    <div class="endpoint">
        <span class="method">GET</span> <code>/v1/tasks/{id}</code>
        <span style="margin-left:12px;color:#666">查询单个任务状态</span>
    </div>
    <div class="endpoint">
        <span class="method">PUT</span> <code>/v1/tasks/{id}/status</code>
        <span style="margin-left:12px;color:#666">更新任务状态（内部用）</span>
    </div>

    <h2>快速开始</h2>
    <pre>curl -X POST https://api.humangates.com/v1/tasks \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "type": "company_registration",
    "params": {
      "city": "石家庄",
      "company_name": "示例科技有限公司"
    }
  }'</pre>

    <h2>文档</h2>
    <p>交互式 API 文档：<a href="/docs">Swagger UI</a></p>
    <p>替代格式：<a href="/redoc">ReDoc</a></p>

    <div class="footer">
        Human Gates v0.1.0 &mdash; humangates.com
    </div>
</body>
</html>"""


app.include_router(tasks.router, prefix=f"{settings.api_prefix}/tasks")
