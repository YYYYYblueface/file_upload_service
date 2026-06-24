import os
import shutil
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, CHUNK_SIZE
from app.models import File, UploadChunk
from app.utils.validators import (
    compute_sha256,
    compute_file_sha256,
    get_unique_filename,
    get_file_extension,
)


def save_uploaded_file(file_data: bytes, original_filename: str, mime_type: str) -> tuple[str, str]:
    """保存上传文件到磁盘，返回(唯一文件名, 存储路径)"""
    unique_name, ext = get_unique_filename(original_filename)
    mime_subdir = mime_type.split("/")[0] if "/" in mime_type else "other"
    target_dir = UPLOAD_DIR / mime_subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    storage_path = str(target_dir / unique_name)
    with open(storage_path, "wb") as f:
        f.write(file_data)
    return unique_name, storage_path


def create_file_record(
    db: Session,
    filename: str,
    original_filename: str,
    file_size: int,
    mime_type: str,
    file_hash: str,
    storage_path: str,
    upload_type: str = "full",
    is_completed: bool = True,
) -> File:
    """创建文件数据库记录"""
    file_record = File(
        filename=filename,
        original_filename=original_filename,
        file_size=file_size,
        mime_type=mime_type,
        file_hash=file_hash,
        storage_path=storage_path,
        upload_type=upload_type,
        is_completed=is_completed,
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


def get_file_by_hash(db: Session, file_hash: str) -> Optional[File]:
    """根据哈希值查找文件"""
    return db.query(File).filter(File.file_hash == file_hash, File.is_completed == True).first()


def get_file_by_id(db: Session, file_id: int) -> Optional[File]:
    """根据ID查找文件"""
    return db.query(File).filter(File.id == file_id).first()


def list_files(db: Session, page: int = 1, page_size: int = 20) -> tuple[list[File], int]:
    """分页列出文件"""
    query = db.query(File).filter(File.is_completed == True).order_by(File.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def delete_file(db: Session, file_id: int) -> bool:
    """删除文件记录和磁盘文件"""
    file_record = get_file_by_id(db, file_id)
    if not file_record:
        return False
    # 删除磁盘文件
    if os.path.exists(file_record.storage_path):
        os.remove(file_record.storage_path)
    # 删除数据库记录
    db.delete(file_record)
    db.commit()
    return True


def save_chunk(
    db: Session,
    file_id: int,
    chunk_index: int,
    chunk_data: bytes,
    original_filename: str,
) -> UploadChunk:
    """保存分片到临时目录"""
    chunk_hash = compute_sha256(chunk_data)
    temp_dir = UPLOAD_DIR / "temp" / str(file_id)
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = str(temp_dir / f"chunk_{chunk_index}")

    with open(temp_path, "wb") as f:
        f.write(chunk_data)

    chunk = UploadChunk(
        file_id=file_id,
        chunk_index=chunk_index,
        chunk_size=len(chunk_data),
        chunk_hash=chunk_hash,
        temp_path=temp_path,
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def get_chunk_count(db: Session, file_id: int) -> int:
    """获取已上传的分片数量"""
    return db.query(UploadChunk).filter(UploadChunk.file_id == file_id).count()


def merge_chunks(db: Session, file_id: int, original_filename: str, mime_type: str) -> File:
    """合并所有分片为完整文件"""
    chunks = (
        db.query(UploadChunk)
        .filter(UploadChunk.file_id == file_id)
        .order_by(UploadChunk.chunk_index)
        .all()
    )

    unique_name, ext = get_unique_filename(original_filename)
    mime_subdir = mime_type.split("/")[0] if "/" in mime_type else "other"
    target_dir = UPLOAD_DIR / mime_subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    storage_path = str(target_dir / unique_name)

    with open(storage_path, "wb") as outfile:
        for chunk in chunks:
            with open(chunk.temp_path, "rb") as infile:
                outfile.write(infile.read())

    file_hash = compute_file_sha256(storage_path)
    total_size = os.path.getsize(storage_path)

    # 清理临时文件
    temp_dir = UPLOAD_DIR / "temp" / str(file_id)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    # 删除旧的分片记录
    db.query(UploadChunk).filter(UploadChunk.file_id == file_id).delete()

    file_record = create_file_record(
        db=db,
        filename=unique_name,
        original_filename=original_filename,
        file_size=total_size,
        mime_type=mime_type,
        file_hash=file_hash,
        storage_path=storage_path,
        upload_type="chunk",
        is_completed=True,
    )
    return file_record