from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Anthropic API
    anthropic_api_key: str = ""
    model: str = "claude-haiku-4-5-20251001"

    # Paths
    data_dir: str = "/app/data/raw"
    vs_dir: str = "/app/data/vectorstore"
    history_file: str = "/app/data/history.json"

    # RAG
    chunk_size: int = 500
    chunk_overlap: int = 80
    top_k: int = 6
    embed_model: str = "all-MiniLM-L6-v2"

    # LLM
    max_tokens: int = 1024
    temperature: float = 0.3

    class Config:
        env_file = "../.env"


cfg = Settings()
