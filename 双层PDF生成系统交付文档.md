# 文档 OCR 处理系统 交付文档

> **版本**: v2.0  
> **日期**: 2026-06-18  
> **环境**: 算力服务器 `10.19.26.153` + 应用服务器 `10.19.26.148`

---

## 1. 系统概述

本系统将扫描版 PDF / 图片转换为多种可用格式。核心功能：

- **可搜索 PDF** — 保留原始图像视觉，叠加 OCR 隐藏文字层，支持 Ctrl+F 搜索和复制
- **多格式输出** — 一次处理同时生成 PDF / TIFF / JPEG / TXT / MD / JSON，按格式分目录存放
- **双引擎 OCR** — PaddleOCR-VL（文字检测 + 精确坐标）+ MinerU（文档结构解析 + 阅读顺序）
- **批量处理** — 支持服务器目录批量扫描和本地上传两种模式

识别引擎采用百度开源的 **PaddleOCR-VL 0.9B**，在 OmniDocBench V1.5 综合评测中得分 92.6。

---

## 2. 系统架构

```mermaid
graph TB
    subgraph Browser["🌐 浏览器"]
        UI["React SPA<br/>Ant Design 6"]
    end

    subgraph Docker["🐳 Docker Compose (:9010)"]
        Nginx["Nginx 反向代理"]
        Backend["FastAPI Backend"]
        DB[("SQLite jobs.db")]
        FM["Formatters<br/>6 种格式"]
    end

    subgraph Compute["🖥️ 算力服务器 10.19.26.153"]
        PO["PaddleOCR-VL<br/>:8080"]
        MU["MinerU<br/>:8000"]
        GPU["Tesla T4 15GB"]
    end

    UI -->|HTTP :9010| Nginx
    Nginx -->|/api/*| Backend
    Backend <--> DB
    Backend --> FM
    Backend -->|layout-parsing| PO
    Backend -->|file_parse| MU
    PO --> GPU
    MU --> GPU
```

---

## 3. 服务器环境

### 3.1 算力服务器（推理节点）

| 项目 | 信息 |
|------|------|
| IP | 10.19.26.153 |
| GPU | NVIDIA Tesla T4 · 15360 MiB |
| CUDA | 12.2 |
| 部署方式 | Docker Compose |
| 服务 | PaddleOCR-VL (:8080) + MinerU (:8000, :7860) |

### 3.2 应用服务器（Web 服务节点）

| 项目 | 信息 |
|------|------|
| IP | 10.19.26.148 |
| CPU | 8 核，无 GPU |
| 内存 | 32 GB |
| 部署方式 | Docker Compose (`/opt/pdf2searchable-v2/`) |
| 访问端口 | 9010 |
| 数据存储 | Docker 命名卷（持久化，启停不丢失） |

> 旧版 (systemd 服务, 9008 端口) 已停用，由 Docker 版 (9010) 替代。

---

## 4. 算力服务器部署

### 4.1 PaddleOCR-VL

```
/opt/paddleocr-vl/
├── compose.yaml
└── pipeline_config_vllm.yaml
```

```bash
cd /opt/paddleocr-vl && docker compose up -d
curl http://localhost:8080/health    # 验证
```

**API**: `POST /layout-parsing` (JSON, base64 编码文件)

### 4.2 MinerU

```bash
cd /opt/mineru-server && docker compose --profile api --profile gradio up -d
curl http://localhost:8000/health    # 验证
```

**API**: `POST /file_parse` (multipart/form-data 文件上传)

---

## 5. 应用服务器部署

### 5.1 目录结构

```
/opt/pdf2searchable-v2/
├── docker-compose.yml
├── .env                     # 环境变量配置
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI 路由
│       ├── ocr.py           # PaddleOCR + MinerU 客户端
│       ├── tasks.py         # 处理任务调度
│       ├── db.py            # SQLite 数据库
│       ├── models.py        # 数据模型
│       ├── config.py        # 配置
│       └── formatters/      # 6 种输出格式
│           ├── pdf.py       # 可搜索 PDF
│           ├── tiff.py      # TIFF 归档
│           ├── jpeg.py      # JPEG 预览
│           ├── txt.py       # 纯文本
│           ├── md.py        # Markdown
│           └── json.py      # JSON 数据
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.tsx    # 仪表盘
│       │   ├── SingleUpload.tsx # 单页上传
│       │   └── BatchProcess.tsx # 批量处理
│       └── components/          # UI 组件
```

### 5.2 启动与管理

```bash
cd /opt/pdf2searchable-v2

# 首次构建启动
docker compose up -d --build

# 日常启动/停止（保留容器）
docker compose start
docker compose stop

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f nginx
```

### 5.3 配置

通过 `.env` 文件配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PADDLEOCR_URL` | `http://10.19.26.153:8080` | PaddleOCR 服务地址 |
| `MINERU_URL` | `http://10.19.26.153:8000` | MinerU 服务地址 |
| `PADDLEOCR_TIMEOUT` | `600` | PaddleOCR 超时（秒） |
| `MINERU_TIMEOUT` | `600` | MinerU 超时（秒） |
| `MAX_UPLOAD_SIZE_MB` | `100` | 单文件大小限制 |

### 5.4 数据持久化

Docker Compose 定义了命名卷，数据独立于容器生命周期：

| 卷名 | 挂载路径 | 内容 |
|------|---------|------|
| `uploads` | `/app/uploads/` | 上传文件 + 处理结果 |
| `data` | `/app/data/` | SQLite 数据库（任务记录） |

> `docker compose down` 或 `stop` **不会**删除数据。只有 `docker compose down -v` 才会清除卷。

---

## 6. 处理流程

```mermaid
sequenceDiagram
    participant U as 用户浏览器
    participant N as Nginx :9010
    participant B as FastAPI Backend
    participant P as PaddleOCR-VL :8080
    participant M as MinerU :8000
    participant DB as SQLite

    U->>N: POST /api/upload (PDF/图片)
    N->>B: 转发请求
    B->>B: 保存文件，创建任务记录
    B->>DB: INSERT job (pending)
    
    par PaddleOCR 识别
        B->>P: POST /layout-parsing
        P-->>B: JSON {文字块+坐标}
    and MinerU 解析
        B->>M: POST /file_parse
        M-->>B: JSON {md, content_list}
    end

    B->>B: 调用各格式 Formatter
    B->>DB: UPDATE job (done)
    B-->>N: 返回 {status: done, files: [...]}
    N-->>U: 处理结果 + 下载链接
```

---

## 7. 输出格式

| 格式 | 文件名 | 说明 | 依赖引擎 |
|------|--------|------|---------|
| 可搜索 PDF | `*_searchable.pdf` | 原图 + 透明 OCR 文字覆盖层 | PaddleOCR |
| TIFF 归档 | `*.tiff` | 多页 TIFF，LZW 无损压缩 | 无（纯图像） |
| JPEG 预览 | `*_p{页码}.jpg` | 每页一张 1200px 宽预览图 | 无（纯图像） |
| 纯文本 | `*.txt` | 按 MinerU 阅读顺序提取全部文字 | MinerU |
| Markdown | `*.md` | 保留标题层级、表格结构 | MinerU |
| JSON 数据 | `*.json` | 完整 OCR 数据 + 版式信息 | 两个引擎 |

---

## 8. 批量处理

支持两种模式：

1. **服务器目录** — 输入 NAS/服务器上的目录路径，直接扫描处理
2. **本地上传** — 从电脑浏览器选择文件上传到服务器，再作为批量任务处理

---

## 9. 任务管理

- 处理记录持久化存储在 SQLite 数据库中
- 详情弹窗可查看每个格式的下载链接
- 支持单条删除和批量删除
- 结果文件永久保留在 `uploads` 卷中

---

## 10. 已知限制

| 限制 | 说明 |
|------|------|
| GPU 显存 | Tesla T4 仅 15GB，PaddleOCR + MinerU 占用约 11.7GB，切换场景需停掉其他服务 |
| 并发 | 单队列处理，后续请求排队等待 |
| OCR 超时 | 多页文档处理时间较长，已配置 600 秒超时 |

---

## 11. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-06-12 | 初始版本：PyMuPDF + PaddleOCR，单页 Web 服务，端口 9008 |
| **v2.0** | **2026-06-18** | Docker 化重构：FastAPI + React，6 格式输出，MinerU 集成，端口 9010 |

---

*文档生成于 2026-06-18 · PaddleOCR-VL · MinerU 3.1.9 · PyMuPDF 1.25*
