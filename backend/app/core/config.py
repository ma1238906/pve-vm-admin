from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PVE VDI"
    
    # PVE Configuration
    PVE_HOST: str = "127.0.0.1"
    PVE_PORT: int = 8006
    PVE_USER: str = "root@pam"
    PVE_TOKEN_NAME: str = ""
    PVE_TOKEN_VALUE: str = ""
    PVE_VERIFY_SSL: bool = False
    
    # Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./pve_vdi.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
