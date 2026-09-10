import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "FinAgent")
    ENV: str = os.getenv("ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretfinagentjwtkeypleasechangethisinproduction")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./finagent.db")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    AGENT_CONFIDENCE_THRESHOLD: float = float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", "0.75"))
    ANOMALY_SENSITIVITY: float = float(os.getenv("ANOMALY_SENSITIVITY", "0.70"))
    PROACTIVE_MONITOR_INTERVAL_MINUTES: int = int(os.getenv("PROACTIVE_MONITOR_INTERVAL_MINUTES", "15"))

settings = Settings()
