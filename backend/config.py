import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'pharmacy_dev.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get("JWT_ACCESS_EXPIRES_HOURS", 8)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get("JWT_REFRESH_EXPIRES_DAYS", 30)))
    JWT_ALGORITHM = "HS256"

    # Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@pharmacy.com")
    ALERT_RECIPIENTS = os.environ.get("ALERT_RECIPIENTS", "admin@pharmacy.com").split(",")

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "prescriptions")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

    # Scheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = os.environ.get("SCHEDULER_TIMEZONE", "UTC")

    # ML Service
    ML_SERVICE_BASE_URL = os.environ.get("ML_SERVICE_BASE_URL", "http://ml-service:8000")
    ML_SERVICE_TIMEOUT = int(os.environ.get("ML_SERVICE_TIMEOUT", 30))
    ML_SERVICE_API_KEY = os.environ.get("ML_SERVICE_API_KEY", "")

    # Business rules
    LOW_STOCK_THRESHOLD = int(os.environ.get("LOW_STOCK_THRESHOLD", 10))
    EXPIRY_ALERT_DAYS = int(os.environ.get("EXPIRY_ALERT_DAYS", 30))

    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    }


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
