# 通用文件 + 图片上传管理接口服务

FastAPI + MySQL + Redis 实现的通用文件上传管理服务，支持大文件分片上传、图片压缩、文件类型校验、Redis文件去重。

## 项目功能

✅ **完整文件上传** - 支持小文件一次性完整上传

✅ **大文件分片上传** - 支持GB级大文件，分块上传后合并

✅ **图片压缩** - 自动缩小图片尺寸、降低质量，节省存储空间

✅ **文件类型校验** - 仅允许指定的MIME类型上传，提高安全性

✅ **Redis文件去重** - 通过SHA256哈希检查已上传文件，避免重复存储

✅ **文件列表分页** - 支持分页查询已上传文件

✅ **静态资源访问** - 本地可通过 `/uploads/xxx` 访问，支持Nginx托管

✅ **删除功能** - 删除数据库记录和磁盘文件

## 技术栈

| 技术 | 用途 |
|------|------|
| **FastAPI** | Web框架，自动生成API文档 |
| **SQLAlchemy** | ORM数据库操作 |
| **MySQL** | 存储文件元数据 |
| **Redis** | 缓存文件哈希去重 |
| **Pillow** | 图片压缩处理 |
| **Python-Multipart** | 文件上传解析 |
| **Nginx** | 静态资源托管（生产环境） |
| **Git** | 版本控制 |

## 开发工具

- **VSCode** - 代码编辑器
- **DBeaver** - MySQL数据库可视化管理工具
- **Redis Desktop Manager** - Redis可视化管理工具

## 快速开始

### 环境要求

- Python 3.9+
- MySQL 8.0+
- Redis 6.0+

### 1. 克隆项目

```bash
git clone https://github.com/[你的用户名]/file_upload_service.git
cd file_upload_service
```

### 2. 创建虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 创建数据库

在MySQL中创建数据库：

```sql
CREATE DATABASE file_upload_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

程序启动时会自动创建所需的表结构。

### 5. 配置环境变量（可选）

创建 `.env` 文件：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=file_upload_db

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

默认连接 `root:root` @ `127.0.0.1`

### 6. 启动服务

开发模式：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

生产模式：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. 访问服务

- **API文档**: http://127.0.0.1:8000/docs
- **ReDoc文档**: http://127.0.0.1:8000/redoc
- **健康检查**: http://127.0.0.1:8000/health

## API 接口说明

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/files/upload` | POST | 完整上传文件 |
| `/api/v1/files/chunk/init` | POST | 初始化分片上传 |
| `/api/v1/files/chunk/upload` | POST | 上传单个分片 |
| `/api/v1/files/chunk/merge` | POST | 合并分片完成上传 |
| `/api/v1/files/check` | GET | 检查文件是否存在（去重） |
| `/api/v1/files/list` | GET | 文件列表（分页） |
| `/api/v1/files/{file_id}` | GET | 获取文件详情 |
| `/api/v1/files/{file_id}` | DELETE | 删除文件 |

### 使用示例

#### 1. 完整上传

使用 `multipart/form-data`，key 为 `file`，在参数中勾选 `compress` 可压缩图片。

#### 2. 分片上传流程

1. 调用 `chunk/init` -> 获取 `file_id`
2. 循环调用 `chunk/upload` 上传每个分片（提供 `file_id` + `chunk_index` + `chunk` 文件）
3. 所有分片上传完成后调用 `chunk/merge`

#### 3. 客户端去重优化

上传前在客户端计算文件 SHA256，调用 `/api/v1/files/check?file_hash=xxx`：

- 如果返回 `exists: true`，直接使用返回文件信息，无需上传
- 如果返回 `exists: false`，再执行上传流程

## 数据库表结构

### `files` 表 - 已完成文件元数据表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT | 主键，自增 |
| `filename` | VARCHAR(255) | 存储文件名（UUID生成，避免冲突） |
| `original_filename` | VARCHAR(500) | 用户上传时的原始文件名 |
| `file_size` | BIGINT | 文件大小（字节） |
| `mime_type` | VARCHAR(100) | 文件MIME类型 |
| `file_hash` | VARCHAR(64) | 文件SHA256哈希（用于去重） |
| `storage_path` | VARCHAR(500) | 磁盘存储完整路径 |
| `upload_type` | VARCHAR(20) | 上传方式：`full`=完整上传，`chunk`=分片上传 |
| `is_completed` | BOOLEAN | 是否上传完成 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |

### `upload_chunks` 表 - 分片上传临时记录表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT | 主键，自增 |
| `file_id` | INTEGER | 关联临时文件ID |
| `chunk_index` | INTEGER | 分片序号（从0开始） |
| `chunk_size` | BIGINT | 分片大小（字节） |
| `chunk_hash` | VARCHAR(64) | 分片SHA256 |
| `temp_path` | VARCHAR(500) | 分片临时存储路径 |
| `created_at` | DATETIME | 创建时间 |

**表关系说明：**
- 分片上传时：`files` 先插入一条 `is_completed=false` 的临时记录
- 合并成功后：删除临时记录，创建一条新的 `is_completed=true` 的完整记录，同时删除 `upload_chunks` 中的所有分片
- 正常上传：只有 `files` 记录，不会产生 `upload_chunks`

## Redis 缓存结构

| Key | 类型 | Value |
|-----|------|-------|
| `file:hash:{SHA256}` | String | JSON序列化的 FileOut 对象 |

作用：快速命中已上传文件，不需要查询数据库，提高去重速度。

## Nginx 静态资源托管配置（生产环境）

```nginx
location ~ ^/uploads/ {
    root /path/to/file_upload_service;
    expires 7d;
    add_header Cache-Control public;
    access_log off;
}

location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

这样：
- `http://your-domain/uploads/...` 直接由Nginx返回静态文件，不经过FastAPI
- 其他接口由Nginx代理给FastAPI应用

## 配置说明

在 `app/config.py` 中可以调整以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CHUNK_SIZE` | 5MB | 分片大小 |
| `MAX_FILE_SIZE` | 500MB | 最大文件大小 |
| `IMAGE_MAX_WIDTH` | 1920 | 图片压缩最大宽度 |
| `IMAGE_MAX_HEIGHT` | 1080 | 图片压缩最大高度 |
| `IMAGE_QUALITY` | 85 | JPEG保存质量 |

## 项目结构

```
file_upload_service/
├── app/
│   ├── __init__.py
│   ├── config.py           # 配置
│   ├── database.py         # 数据库连接
│   ├── main.py             # FastAPI入口
│   ├── redis_client.py     # Redis连接
│   ├── models/             # 数据库模型
│   │   └── __init__.py
│   ├── routers/            # API路由
│   │   └── __init__.py
│   ├── schemas/            # Pydantic模型
│   │   └── __init__.py
│   ├── services/           # 业务逻辑
│   │   ├── __init__.py
│   │   └── image_service.py
│   └── utils/              # 工具函数
│       ├── __init__.py
│       └── validators.py
├── uploads/                # 上传文件存储目录
│   └── temp/               # 分片临时目录
├── .gitignore
├── README.md
└── requirements.txt
```

## 做这个项目的目的

这个项目是一个典型的**实战型工具项目**，目的是：

1. **练习FastAPI框架** - 掌握现代Python Web开发
2. **理解大文件上传方案** - 学习分片上传技术原理
3. **学习缓存去重思路** - 通过Redis实现秒传功能
4. **图片处理实践** - 实现图片压缩优化
5. **了解生产环境部署** - Nginx静态托管 + 反向代理模式
6. **完整项目开发流程** - 从零搭建到部署上线的完整流程

## 项目亮点

- ✅ **完整的权限友好性**：只允许配置的文件类型上传，避免安全风险
- ✅ **节省存储空间**：相同哈希文件只存储一份，Redis缓存加速去重检查
- ✅ **支持超大文件**：不管多大文件都可以分块上传，不会占用过多内存
- ✅ **图片自动优化**：上传图片自动压缩，节省带宽和存储空间
- ✅ **自动文档**：FastAPI自动生成Swagger文档，可在线调试

## License

MIT
