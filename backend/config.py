import os
from pydantic import BaseModel


class Settings(BaseModel):
    APP_NAME: str = "Retail Sales & Inventory Copilot"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")


settings = Settings()
