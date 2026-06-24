import hashlib
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.redis_client import get_redis
from app.schemas import (
    FileOut,
    FileListOut,
    ChunkUploadInit,
    ChunkUploadInitOut,
    ChunkUploadOut,
    ChunkMergeOut,
    DeleteOut,
    DedupCheckOut,
)
from app.services import (
    save_uploaded_file,
    create_file_record,
    get_file_by_hash,
    get_file_by_id,
    list_files,
    delete_file,
    save_chunk,
    get_chunk_count,
    merge_chunks,
)
from app.services.image_service import compress_image
from app.utils.validators import (
    validate_file_type,
    validate_file_size,
    compute_sha256,
    is_image_type,
)

router = APIRouter(prefix="/api/v1/files", tags=["文件管理"])


@router.post("/upload", response_model=FileOut, summary="完整上传文件")
async def upload_file(
    file: UploadFile = File(...),
    compress: bool = Query(False, description="是否压缩图片"),
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """上传文件（支持完整上传和图片压缩）"""
    # 读取文件内容
    file_data = await file.read()
    file_size = len(file_data)

    # 校验文件类型
    if not validate_file_type(file.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}",
        )

    # 校验文件大小
    if not validate_file_size(file_size):
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制({file_size} bytes)",
        )

    # 计算文件哈希
    file_hash = compute_sha256(file_data)

    # Redis去重检查
    cached = await redis.get(f"file:hash:{file_hash}")
    if cached:
        return FileOut.model_validate(cached)

    # 数据库去重检查
    existing = get_file_by_hash(db, file_hash)
    if existing:
        await redis.set(f"file:hash:{file_hash}", FileOut.model_validate(existing).model_dump_json())
        return FileOut.model_validate(existing)

    # 保存文件
    original_filename = file.filename or "unknown"
    filename, storage_path = save_uploaded_file(file_data, original_filename, file.content_type or "application/octet-stream")

    # 图片压缩
    if compress and is_image_type(file.content_type):
        compress_image(storage_path, storage_path)

    # 创建数据库记录
    file_record = create_file_record(
        db=db,
        filename=filename,
        original_filename=original_filename,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        file_hash=file_hash,
        storage_path=storage_path,
    )

    # 缓存到Redis
    await redis.set(f"file:hash:{file_hash}", FileOut.model_validate(file_record).model_dump_json())

    return FileOut.model_validate(file_record)


@router.post("/chunk/init", response_model=ChunkUploadInitOut, summary="初始化分片上传")
async def init_chunk_upload(body: ChunkUploadInit, db: Session = Depends(get_db)):
    """初始化分片上传，返回临时文件ID"""
    if not validate_file_type(body.mime_type):
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {body.mime_type}")

    if not validate_file_size(body.total_size):
        raise HTTPException(status_code=400, detail=f"文件大小超过限制({body.total_size} bytes)")

    from app.models import File as FileModel
    from app.config import CHUNK_SIZE

    temp_file = FileModel(
        filename="",
        original_filename=body.original_filename,
        file_size=body.total_size,
        mime_type=body.mime_type,
        file_hash="",
        storage_path="",
        upload_type="chunk",
        is_completed=False,
    )
    db.add(temp_file)
    db.commit()
    db.refresh(temp_file)

    return ChunkUploadInitOut(file_id=temp_file.id, chunk_size=CHUNK_SIZE)


@router.post("/chunk/upload", response_model=ChunkUploadOut, summary="上传分片")
async def upload_chunk(
    file_id: int = Query(..., description="临时文件ID"),
    chunk_index: int = Query(..., description="分片序号"),
    chunk: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传单个分片"""
    chunk_data = await chunk.read()
    save_chunk(
        db=db,
        file_id=file_id,
        chunk_index=chunk_index,
        chunk_data=chunk_data,
        original_filename=chunk.filename or "unknown",
    )

    return ChunkUploadOut(
        chunk_index=chunk_index,
        received=True,
        progress=f"{chunk_index + 1}/?",
    )


@router.post("/chunk/merge", response_model=ChunkMergeOut, summary="合并分片")
async def merge_chunk_upload(
    file_id: int = Query(..., description="临时文件ID"),
    compress: bool = Query(False, description="是否压缩图片"),
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """合并所有已上传的分片"""
    from app.models import File as FileModel

    temp_file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.is_completed == False).first()
    if not temp_file:
        raise HTTPException(status_code=404, detail="未找到分片上传记录")

    file_record = merge_chunks(
        db=db,
        file_id=file_id,
        original_filename=temp_file.original_filename,
        mime_type=temp_file.mime_type,
    )

    # 删除临时记录
    db.delete(temp_file)
    db.commit()

    # 图片压缩
    if compress and is_image_type(file_record.mime_type):
        compress_image(file_record.storage_path, file_record.storage_path)

    # 缓存
    await redis.set(
        f"file:hash:{file_record.file_hash}",
        FileOut.model_validate(file_record).model_dump_json(),
    )

    return ChunkMergeOut(
        file_id=file_record.id,
        file=FileOut.model_validate(file_record),
        message="分片合并完成",
    )


@router.get("/check", response_model=DedupCheckOut, summary="检查文件是否已存在(去重)")
async def check_dedup(
    file_hash: str = Query(..., description="文件SHA256哈希"),
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """通过文件哈希检查文件是否已上传（去重检查）"""
    cached = await redis.get(f"file:hash:{file_hash}")
    if cached:
        import json
        return DedupCheckOut(exists=True, file=FileOut(**json.loads(cached)), message="文件已存在(Redis缓存命中)")

    existing = get_file_by_hash(db, file_hash)
    if existing:
        await redis.set(f"file:hash:{file_hash}", FileOut.model_validate(existing).model_dump_json())
        return DedupCheckOut(exists=True, file=FileOut.model_validate(existing), message="文件已存在")

    return DedupCheckOut(exists=False, message="文件不存在，可以上传")


@router.get("/list", response_model=FileListOut, summary="文件列表")
async def list_uploaded_files(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """分页获取已上传的文件列表"""
    items, total = list_files(db, page=page, page_size=page_size)
    return FileListOut(
        total=total,
        items=[FileOut.model_validate(item) for item in items],
    )


@router.get("/{file_id}", response_model=FileOut, summary="获取文件详情")
async def get_file_detail(file_id: int, db: Session = Depends(get_db)):
    """获取单个文件详情"""
    file_record = get_file_by_id(db, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileOut.model_validate(file_record)


@router.delete("/{file_id}", response_model=DeleteOut, summary="删除文件")
async def delete_uploaded_file(file_id: int, db: Session = Depends(get_db), redis=Depends(get_redis)):
    """删除文件及其记录"""
    file_record = get_file_by_id(db, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    await redis.delete(f"file:hash:{file_record.file_hash}")
    success = delete_file(db, file_id)

    if success:
        return DeleteOut(message="文件删除成功")
    raise HTTPException(status_code=500, detail="删除失败")