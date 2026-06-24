import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"

# 数据库配置
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "yourpassword")
DB_NAME = os.getenv("DB_NAME", "file_upload_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Redis配置
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# 分片上传配置
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB

# 允许的文件类型
ALLOWED_MIME_TYPES = {
    # 图片
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp",
    # 文档
    "application/pdf", "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # 压缩包
    "application/zip", "application/x-rar-compressed", "application/x-7z-compressed",
    # 音视频
    "video/mp4", "audio/mpeg", "audio/wav",
}

# 图片压缩配置
IMAGE_MAX_WIDTH = 1920
IMAGE_MAX_HEIGHT = 1080
IMAGE_QUALITY = 85

# 文件大小限制
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
