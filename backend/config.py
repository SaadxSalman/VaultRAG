from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VaultRAG"
    api_host: str = "127.0.0.1"
    api_port: int = 8765
    vaultrag_data_dir: Path = Path("./data")
    vaultrag_index_dir: Path = Path("./data/index")
    vaultrag_upload_dir: Path = Path("./data/uploads")
    vaultrag_max_file_mb: int = 25
    vaultrag_top_k: int = 5
    vaultrag_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vaultrag_generation_model: str = "unsloth/Phi-3.5-mini-instruct-bnb-4bit"
    vaultrag_enable_generation: bool = False
    vaultrag_ner_model: str = ""
    vaultrag_enable_ner: bool = False
    vaultrag_audit_enabled: bool = True
    vaultrag_max_new_tokens: int = 384
    vaultrag_log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def ensure_directories(self) -> None:
        for path in (self.vaultrag_data_dir, self.vaultrag_index_dir, self.vaultrag_upload_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
