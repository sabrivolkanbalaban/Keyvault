import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LDAP
    LDAP_SERVER = os.environ.get("LDAP_SERVER", "ldap://dc01.company.local")
    LDAP_DOMAIN = os.environ.get("LDAP_DOMAIN", "COMPANY")
    LDAP_BASE_DN = os.environ.get("LDAP_BASE_DN", "DC=company,DC=local")
    LDAP_BIND_USER = os.environ.get("LDAP_BIND_USER", "")
    LDAP_BIND_PASSWORD = os.environ.get("LDAP_BIND_PASSWORD", "")
    LDAP_USER_SEARCH_BASE = os.environ.get("LDAP_USER_SEARCH_BASE", LDAP_BASE_DN)
    LDAP_GROUP_SEARCH_BASE = os.environ.get("LDAP_GROUP_SEARCH_BASE", LDAP_BASE_DN)

    # Role Mapping
    LDAP_ADMIN_GROUPS = os.environ.get("LDAP_ADMIN_GROUPS", "").split(",")
    LDAP_USER_GROUPS = os.environ.get("LDAP_USER_GROUPS", "").split(",")
    LDAP_READONLY_GROUPS = os.environ.get("LDAP_READONLY_GROUPS", "").split(",")

    # Oracle Database
    ORACLE_HOST = os.environ.get("ORACLE_HOST", "")
    ORACLE_PORT = int(os.environ.get("ORACLE_PORT", "1521"))
    ORACLE_SERVICE = os.environ.get("ORACLE_SERVICE", "")
    ORACLE_USER = os.environ.get("ORACLE_USER", "")
    ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "")

    # Session
    SESSION_TIMEOUT_MINUTES = int(os.environ.get("SESSION_TIMEOUT_MINUTES", "30"))
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.environ.get("SESSION_TIMEOUT_MINUTES", "30"))
    )
    SESSION_REFRESH_EACH_REQUEST = True
    REMEMBER_COOKIE_DURATION = timedelta(hours=8)
    REMEMBER_COOKIE_HTTPONLY = True

    # Security
    MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES = int(os.environ.get("LOCKOUT_DURATION_MINUTES", "15"))

    # Pagination
    ITEMS_PER_PAGE = 25


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///keyvault.db"
    )
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
