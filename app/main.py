from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.database import init_db
from app.routers import tasks, files, services, operations, suppliers, customers

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Human Gates API — AI agent 的物理世界任务交付层",
)

WWW_DIR = Path(__file__).resolve().parent.parent / "www"


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def root():
    return (WWW_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api-docs", response_class=HTMLResponse)
def api_docs():
    return (WWW_DIR / "api-docs.html").read_text(encoding="utf-8")


@app.get("/pricing", response_class=HTMLResponse)
def pricing():
    return (WWW_DIR / "pricing.html").read_text(encoding="utf-8")


@app.get("/supplier-register", response_class=HTMLResponse)
def supplier_register():
    return (WWW_DIR / "supplier-register.html").read_text(encoding="utf-8")


@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/", response_class=HTMLResponse)
def admin_panel():
    return (WWW_DIR / "admin" / "index.html").read_text(encoding="utf-8")


# Static assets: CSS, JS, images
app.mount("/css", StaticFiles(directory=str(WWW_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(WWW_DIR / "js")), name="js")

app.include_router(tasks.router, prefix=f"{settings.api_prefix}/tasks")
app.include_router(files.router, prefix=f"{settings.api_prefix}/tasks")
app.include_router(services.router, prefix=f"{settings.api_prefix}/services")
app.include_router(operations.router, prefix=f"{settings.api_prefix}/tasks")
app.include_router(suppliers.router, prefix=f"{settings.api_prefix}/suppliers")
app.include_router(customers.router, prefix=f"{settings.api_prefix}/customers")
