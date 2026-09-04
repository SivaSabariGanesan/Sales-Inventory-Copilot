import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file automatically if present
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val


class Settings(BaseModel):
    APP_NAME: str = "Retail Sales & Inventory Copilot"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # Database Configuration
    @classmethod
    def get_db_path(cls) -> Path:
        is_serverless = bool(
            os.getenv("VERCEL")
            or os.getenv("VERCEL_ENV")
            or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
            or os.getenv("LAMBDA_TASK_ROOT")
        )
        if is_serverless:
            import shutil
            tmp_db = Path("/tmp/retail.db")
            if not tmp_db.exists() or tmp_db.stat().st_size == 0:
                possible_srcs = [
                    BASE_DIR / "data" / "retail.db",
                    Path(__file__).resolve().parent.parent / "data" / "retail.db",
                    Path("/var/task/data/retail.db"),
                    Path.cwd() / "data" / "retail.db",
                    Path("data/retail.db"),
                ]
                for src_db in possible_srcs:
                    if src_db.exists() and src_db.stat().st_size > 0:
                        tmp_db.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            shutil.copyfile(src_db, tmp_db)
                            break
                        except Exception as e:
                            print(f"Failed copying DB from {src_db} to /tmp: {e}")
            return tmp_db
        return BASE_DIR / os.getenv("DB_PATH", "data/retail.db")

    @property
    def DB_PATH(self) -> Path:
        return self.get_db_path()

    # Authentication & Security Configuration (Environment variables only)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "retail-copilot-dev-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


settings = Settings()
