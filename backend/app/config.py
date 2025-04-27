from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Asha Chatbot API"
    api_prefix: str = "/api"
    debug: bool = False
    session_timeout_minutes: int = 30
    job_api_url: str = "https://api.jobsforher.com/jobs"
    event_api_url: str = "https://api.jobsforher.com/events"
    
    class Config:
        env_file = ".env"

settings = Settings()