from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "Human Gates API"
    app_version: str = "0.5.0"
    master_api_key: str = ""
    admin_api_key: str = ""
    database_url: str = "sqlite:///./humangates.db"
    api_prefix: str = "/v1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
