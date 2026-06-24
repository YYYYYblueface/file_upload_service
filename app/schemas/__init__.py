from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FileOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    file_hash: str
    storage_path: str
    upload_type: str
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileListOut(BaseModel):
    total: int
    items: list[FileOut]


class ChunkUploadInit(BaseModel):
    original_filename: str = Field(..., description="原始文件名")
    total_size: int = Field(..., description="文件总大小(字节)")
    mime_type: str = Field(..., description="MIME类型")
    total_chunks: int = Field(..., description="总分片数")


class ChunkUploadInitOut(BaseModel):
    file_id: int
    chunk_size: int  # 分片大小


class ChunkUploadOut(BaseModel):
    chunk_index: int
    received: bool
    progress: str  # 如 "3/10"


class ChunkMergeOut(BaseModel):
    file_id: int
    file: FileOut
    message: str


class DedupCheckOut(BaseModel):
    exists: bool
    file: Optional[FileOut] = None
    message: str


class DeleteOut(BaseModel):
    message: str