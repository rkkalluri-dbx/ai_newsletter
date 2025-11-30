"""Flask configuration settings."""
import os
from typing import List


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-prod")
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Databricks Unity Catalog settings
    DATABRICKS_SERVER_HOSTNAME = os.environ.get("DATABRICKS_SERVER_HOSTNAME", "")
    DATABRICKS_HTTP_PATH = os.environ.get("DATABRICKS_HTTP_PATH", "")
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    DATABRICKS_CATALOG = os.environ.get("DATABRICKS_CATALOG", "main")
    DATABRICKS_SCHEMA = os.environ.get("DATABRICKS_SCHEMA", "gpc_reliability")

    # Pagination defaults
    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class StagingConfig(Config):
    """Staging configuration."""

    DEBUG = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "prod-secret-key-change-me")


config = {
    "development": DevelopmentConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
