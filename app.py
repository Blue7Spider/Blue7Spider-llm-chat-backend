import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr

class ApplicationSettings(BaseSettings):
    # API Kulcsok titkosított kezelése SecretStr-rel (megelőzi a logokba való véletlen kiírást)
    gemini_api_key: SecretStr = Field(alias="GEMINI_API_KEY")
    groq_api_key: SecretStr = Field(alias="GROQ_API_KEY")
    
    # Adatbázis elérhetőség
    database_url: str = Field(
        default="sqlite+aiosqlite:///./chat_application.db", 
        alias="DATABASE_URL"
    )
    
    # Biztonsági beállítások
    allowed_cors_origins: list[str] = ["http://localhost:3000", "https://chat.domain.com"]
    
    # LLM környezeti alapbeállítások
    max_context_message_limit: int = Field(default=10, alias="CONTEXT_MESSAGE_LIMIT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Globálisan elérhető példány
settings = ApplicationSettings()