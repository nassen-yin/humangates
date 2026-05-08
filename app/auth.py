from fastapi import Header, HTTPException, Depends
from app.config import get_settings, Settings


async def verify_api_key(
    x_api_key: str = Header(..., description="开发者 API Key"),
    settings: Settings = Depends(get_settings),
):
    if not settings.master_api_key:
        raise HTTPException(status_code=500, detail="Server not configured: MASTER_API_KEY is empty")
    if x_api_key != settings.master_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


async def verify_admin_key(
    x_admin_key: str = Header(..., description="管理员 Key"),
    settings: Settings = Depends(get_settings),
):
    if not settings.admin_api_key:
        raise HTTPException(status_code=500, detail="Server not configured: ADMIN_API_KEY is empty")
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return x_admin_key
