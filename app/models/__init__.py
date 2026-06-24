from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Integer, func

from app.database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, comment="存储文件名(UUID)")
    original_filename = Column(String(500), nullable=False, comment="原始文件名")
    file_size = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    mime_type = Column(String(100), nullable=False, comment="MIME类型")
    file_hash = Column(String(64), nullable=False, comment="文件SHA256哈希")
    storage_path = Column(String(500), nullable=False, comment="存储路径")
    upload_type = Column(String(20), default="full", comment="上传方式: full=完整上传, chunk=分片上传")
    is_completed = Column(Boolean, default=True, comment="是否上传完成")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class UploadChunk(Base):
    __tablename__ = "upload_chunks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_id = Column(Integer, nullable=False, comment="关联的文件ID(临时)")
    chunk_index = Column(Integer, nullable=False, comment="分片序号(从0开始)")
    chunk_size = Column(BigInteger, nullable=False, comment="分片大小(字节)")
    chunk_hash = Column(String(64), nullable=False, comment="分片SHA256哈希")
    temp_path = Column(String(500), nullable=False, comment="分片临时存储路径")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")