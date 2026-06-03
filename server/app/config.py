import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///../data/easybx.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    server_port: int = int(os.getenv("SERVER_PORT", "220"))
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    ocr_enabled: bool = os.getenv("OCR_ENABLED", "true").lower() == "true"

    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    ocr_max_workers: int = int(os.getenv("OCR_MAX_WORKERS", "2"))
    ocr_timeout_seconds: int = int(os.getenv("OCR_TIMEOUT_SECONDS", "120"))

    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5180,http://127.0.0.1:5180",
    ).split(",")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()
