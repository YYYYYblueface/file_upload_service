import hashlib
from typing import Optional

from app.config import ALLOWED_MIME_TYPES, MAX_FILE_SIZE


def validate_file_type(mime_type: str) -> bool:
    """校验文件类型是否在允许列表中"""
    return mime_type in ALLOWED_MIME_TYPES


def validate_file_size(file_size: int) -> bool:
    """校验文件大小是否超过限制"""
    return file_size <= MAX_FILE_SIZE


def compute_sha256(data: bytes) -> str:
    """计算数据的SHA256哈希值"""
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """计算文件的SHA256哈希值"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_image_type(mime_type: str) -> bool:
    """判断是否为图片类型"""
    return mime_type and mime_type.startswith("image/")


def get_unique_filename(original_filename: str) -> tuple[str, str]:
    """生成唯一的存储文件名"""
    import uuid
    ext = get_file_extension(original_filename)
    unique_name = f"{uuid.uuid4().hex}"
    if ext:
        unique_name = f"{unique_name}.{ext}"
    return unique_name, ext