"""配置层：开发 / 测试 / 生产三套环境，全部差异收敛到此处与 .env。"""
import os
from datetime import timedelta

# server/ 目录
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


class BaseConfig:
    """所有环境公共配置。"""

    # ---------- 安全 ----------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key-please-change")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_NAME = "lf_session"
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Flask-WTF：前后端分离场景下从请求头读取 CSRF Token
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_HEADERS = ["X-CSRFToken", "X-CSRF-Token"]

    # ---------- CORS（开发期 Vite 代理已消除跨域，此处为直连兜底）----------
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
    CORS_ALLOW_HEADERS = ["Content-Type", "X-CSRFToken", "X-CSRF-Token", "Authorization"]
    CORS_EXPOSE_HEADERS = ["X-CSRFToken"]

    # ---------- 数据库：MySQL 8.0 ----------
    _DEFAULT_DB = "mysql+pymysql://root:YOUR_DB_PASSWORD@127.0.0.1:3306/campus_lostfound?charset=utf8mb4"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or _DEFAULT_DB
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 2800,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # ---------- 上传 ----------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "instance/uploads"))
    MAX_CONTENT_LENGTH = _env_int("MAX_UPLOAD_MB", 5) * 1024 * 1024
    ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
    IMAGE_MAGIC = {
        "png": b"\x89PNG\r\n\x1a\n",
        "jpg": b"\xff\xd8\xff",
        "jpeg": b"\xff\xd8\xff",
        "gif": b"GIF8",
        "webp": b"RIFF",
    }

    # ---------- 账号安全 ----------
    LOGIN_MAX_RETRY = _env_int("LOGIN_MAX_RETRY", 5)
    LOGIN_LOCK_MINUTES = _env_int("LOGIN_LOCK_MINUTES", 10)
    PASSWORD_MIN_LEN = _env_int("PASSWORD_MIN_LEN", 8)
    PBKDF2_ITERATIONS = 120_000

    # ---------- 分页 ----------
    ITEMS_PER_PAGE = _env_int("ITEMS_PER_PAGE", 12)

    # ---------- 匹配算法权重 ----------
    MATCH_WEIGHTS = {
        "category": _env_float("W_CATEGORY", 0.25),
        "keyword": _env_float("W_KEYWORD", 0.20),
        "location": _env_float("W_LOCATION", 0.15),
        "time": _env_float("W_TIME", 0.15),
        "feature": _env_float("W_FEATURE", 0.15),
        "text": _env_float("W_TEXT", 0.10),
    }
    MATCH_THRESHOLD = _env_float("MATCH_THRESHOLD", 0.45)
    MATCH_TIME_DECAY_DAYS = 7.0

    # ---------- 校园分区字典（地点归一化与邻近度计算）----------
    CAMPUS_ZONES = {
        "教学楼": ["一教", "二教", "三教", "逸夫楼", "教室", "阶梯教室"],
        "图书馆": ["图书馆", "自习室", "阅览室", "借阅台"],
        "食堂": ["一食堂", "二食堂", "三食堂", "教工餐厅", "食堂"],
        "宿舍区": ["1号楼", "2号楼", "3号楼", "4号楼", "5号楼", "6号楼", "宿舍", "公寓"],
        "运动场": ["操场", "体育馆", "篮球场", "羽毛球场", "游泳馆"],
        "行政楼": ["行政楼", "教务处", "学工处", "保卫处"],
        "校门": ["东门", "南门", "西门", "北门", "校门"],
        "其他": [],
    }
    ZONE_ADJACENCY = {
        "教学楼": ["图书馆", "行政楼"],
        "图书馆": ["教学楼", "宿舍区"],
        "食堂": ["宿舍区", "运动场"],
        "宿舍区": ["食堂", "图书馆", "校门"],
        "运动场": ["食堂", "校门"],
        "行政楼": ["教学楼", "校门"],
        "校门": ["行政楼", "运动场", "宿舍区"],
    }


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    """单元测试：不污染开发库，关闭 CSRF 便于直接 POST。"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL") or (
        "mysql+pymysql://root:YOUR_DB_PASSWORD@127.0.0.1:3306/campus_lostfound_test?charset=utf8mb4"
    )
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "instance", "test_uploads")


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    key = (name or os.getenv("FLASK_ENV", "development")).lower()
    return CONFIG_MAP.get(key, DevelopmentConfig)
