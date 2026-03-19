from pydantic_settings import BaseSettings
from typing import Optional, Set


class Settings(BaseSettings):
    # ---------- 项目基础配置 ----------
    PROJECT_NAME: str = "作文批改系统"
    PROJECT_VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = True

    # ---------- JWT 配置 ----------
    JWT_SECRET_KEY: str  # 从 .env 读取
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # ---------- MySQL 数据库 ----------
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = "123456"
    DATABASE_NAME: str = "essay_grading_system"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    # ---------- 文件上传（你的原始配置）----------
    ALLOWED_EXTENSIONS: str = "png,jpg,jpeg,pdf,docx"
    MAX_FILE_SIZE: int = 52428800  # 50MB

    @property
    def ALLOWED_EXTENSIONS_SET(self) -> Set[str]:
        """将逗号分隔的字符串转换为集合"""
        return {f".{ext}" for ext in self.ALLOWED_EXTENSIONS.split(",")}

    # ---------- 腾讯云OCR（你的原始配置）----------
    TENCENT_SECRET_ID: Optional[str] = None
    TENCENT_SECRET_KEY: Optional[str] = None
    TENCENT_OCR_REGION: str = "ap-guangzhou"

    # ---------- 扣子智能体（你的原始配置）----------
    COZE_API_TOKEN: Optional[str] = None
    COZE_WORKFLOW_ID: Optional[str] = None
    COZE_API_BASE: str = "https://api.coze.cn"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # 忽略.env中多余的字段
    }


settings = Settings()
