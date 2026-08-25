from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str = ""
    groq_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "sehat-sathi-health-docs"
    supabase_url: str = ""
    supabase_key: str = ""
    google_calendar_credentials_json: str = ""
    env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()