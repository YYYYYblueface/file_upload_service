from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="文件上传管理服务",
    description="通用文件 + 图片上传管理接口服务，支持大文件分片上传、图片压缩、文件类型校验、Redis去重",
    version="1.0.0",
    lifespan=lifespan,
)

# 挂载静态文件目录（用于Nginx代理后的直接访问）
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(router)


@app.get("/health", tags=["系统"], summary="健康检查")
async def health_check():
    return {"status": "ok", "service": "文件上传管理服务"}