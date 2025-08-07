from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database Configuration
    database_url: str
    supabase_url: str
    supabase_key: str
    
    # Individual Database Variables (no longer required; use DATABASE_URL instead)
    supabase_db_host: Optional[str] = None
    supabase_db_port: Optional[str] = None
    supabase_db_name: Optional[str] = None
    supabase_db_user: Optional[str] = None
    supabase_db_password: Optional[str] = None
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 1000
    
    # Qdrant Configuration
    qdrant_api_key: str
    qdrant_url: str
    qdrant_collection_name: str = "nutrition-guidelines"
    qdrant_region: Optional[str] = None
    
    # Redis Configuration (optional)
    redis_url: Optional[str] = None
    
    # Development Settings
    debug: bool = True
    environment: str = "development"
    disable_premium_checks: bool = False
    
    # Database Pool Settings
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    
    # File Upload
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "./uploads"
    
    # External Services
    pdf_generation_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 