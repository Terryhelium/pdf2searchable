# 宁波市档案馆文档OCR处理系统

[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb)](https://react.dev/)
[![Ant Design](https://img.shields.io/badge/Ant%20Design-6-1677ff)](https://ant.design/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> 面向档案数字化的文档 OCR 处理系统。支持将扫描版 PDF / 图片转换为可搜索 PDF、TIFF 归档、JPEG 预览、纯文本、Markdown 及 JSON 结构化数据输出。

---

## 功能特性

- **多格式输出** — 一次处理同时生成 PDF / TIFF / JPEG / TXT / MD / JSON，按格式分目录存放
- **双引擎 OCR** — PaddleOCR（文字检测 + 精确坐标）+ MinerU（文档结构解析）
- **仪表盘** — 处理统计概览、今日任务量、成功率
- **批量处理** — 指定源目录，后台逐文件处理，自动记录进度
- **格式按需调用** — 仅对请求的格式调用对应的 OCR 引擎，TIFF/JPEG 无需 OCR
- **深色模式 + 6 种主题色切换**
- **Docker 部署** — 一键启动

---

## 系统架构

```mermaid
graph TB
    subgraph Browser["🌐 浏览器"]
        UI["React SPA<br/>Ant Design 6"]
    end

    subgraph Docker["🐳 Docker Compose"]
        subgraph Nginx["Nginx (:9008)"]
            direction LR
            SPA["静态资源<br/>/*"] 
            Proxy["API 反代<br/>/api/*"]
        end

        subgraph Backend["FastAPI Backend (:8000)"]
            API["API 路由层"]
            OCR["OCRProcessor"]
            DB[("SQLite<br/>jobs.db")]
            FM["Formatters<br/>PDF/TIFF/JPEG/TXT/MD/JSON"]
        end
    end

    subgraph OcrServers["🖥️ OCR 算力服务器 (10.19.26.153)"]
        PO["PaddleOCR<br/>文字检测 + 坐标"]
        MU["MinerU<br/>文档结构解析"]
    end

    UI -->|"HTTP :5173/:9008"| Nginx
    Nginx -->|"/*"| SPA
    Nginx -->|"/api/*"| API
    API --> OCR
    API <--> DB
    OCR --> FM
    OCR -->|"HTTP :8080"| PO
    OCR -->|"HTTP :8000"| MU

    classDef browser fill:#e3f2fd,stroke:#1565c0,color:#1565c0
    classDef docker fill:#fff3e0,stroke:#e65100,color:#e65100
    classDef backend fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32
    classDef ocr fill:#fce4ec,stroke:#c62828,color:#c62828
    classDef db fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a

    class UI browser
    class Nginx,SPA,Proxy docker
    class API,OCR,FM,DB backend
    class PO,MU ocr
    class DB db
```

---

## 处理流程

```mermaid
flowchart LR
    Input["📄 输入文件<br/>PDF/图片"] --> Decide{"需要哪些格式?"}

    Decide -->|PDF| PO[PaddleOCR<br/>文字坐标]
    Decide -->|MD/TXT| MU[MinerU<br/>文档结构]
    Decide -->|JSON| Both["两个引擎都调用"]
    Decide -->|TIFF/JPEG| Skip["跳过OCR<br/>纯图像转换"]

    PO --> Merge["合并 OCR 数据"]
    MU --> Merge
    Both --> Merge
    Skip --> Merge

    Merge --> Format{"逐格式生成输出"}

    Format --> PDF_F["📕 pdf/<br/>可搜索PDF"]
    Format --> TIFF_F["🖼️ tiff/<br/>归档TIFF"]
    Format --> JPG_F["🖼️ jpg/<br/>JPEG预览"]
    Format --> TXT_F["📃 txt/<br/>纯文本"]
    Format --> MD_F["📝 md/<br/>Markdown"]
    Format --> JSON_F["📊 json/<br/>结构化数据"]

    classDef input fill:#e3f2fd,stroke:#1565c0,color:#1565c0
    classDef engine fill:#fff3e0,stroke:#e65100,color:#e65100
    classDef format fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32
    classDef skip fill:#f5f5f5,stroke:#9e9e9e,color:#9e9e9e

    class Input input
    class PO,MU,Both engine
    class PDF_F,TIFF_F,JPG_F,TXT_F,MD_F,JSON_F format
    class Skip skip
```

---

## 快速启动

### 本地开发

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端（另一个终端）
cd frontend
npm install
npm run dev -- --host 0.0.0.0

# 浏览器打开 http://localhost:5173
```

### Docker 部署

```bash
docker compose up -d --build
# 访问 http://<host>:9008
```

---

## 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `PADDLEOCR_URL` | `http://10.19.26.153:8080` | PaddleOCR 服务地址 |
| `MINERU_URL` | `http://10.19.26.153:8000` | MinerU 服务地址 |
| `BACKEND_PORT` | `8000` | 后端监听端口 |
| `MAX_UPLOAD_SIZE_MB` | `100` | 单文件上传大小限制 |
| `DATABASE_PATH` | `./data/jobs.db` | SQLite 数据库路径 |
| `UPLOAD_DIR` | `./uploads` | 上传临时目录 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

完整配置见 `.env.example`。

---

## 输出目录结构

```mermaid
graph LR
    Root["📂 目标目录"] --> PDF["📂 pdf/<br/>📕 document_searchable.pdf"]
    Root --> TIFF["📂 tiff/<br/>🖼️ document.tiff"]
    Root --> JPG["📂 jpg/<br/>🖼️ document_p1.jpg<br/>🖼️ document_p2.jpg"]
    Root --> TXT["📂 txt/<br/>📃 document.txt"]
    Root --> MD["📂 md/<br/>📝 document.md"]
    Root --> JSON["📂 json/<br/>📊 document.json"]

    classDef root fill:#fff3e0,stroke:#e65100,color:#e65100
    classDef dir fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32

    class Root root
    class PDF,TIFF,JPG,TXT,MD,JSON dir
```

| 格式 | 文件名 | 说明 |
|------|--------|------|
| 可搜索 PDF | `*_searchable.pdf` | 原图 + 透明 OCR 文字覆盖层 |
| TIFF 归档 | `*.tiff` | 多页 TIFF，LZW 无损压缩 |
| JPEG 预览 | `*_p{页码}.jpg` | 每页一张预览图 |
| 纯文本 | `*.txt` | 按阅读顺序提取全部文字 |
| Markdown | `*.md` | 保留标题层级、表格结构 |
| JSON 数据 | `*.json` | 完整 OCR 数据 + 版式信息 |

---

## 技术栈

```mermaid
mindmap
  root((宁波市档案馆<br/>文档OCR处理系统))
    前端
      React 19
      TypeScript 6
      Ant Design 6
      Vite 8
    后端
      Python 3.11
      FastAPI 0.136
      uvicorn
      aiosqlite
    OCR引擎
      PaddleOCR
      文字检测+识别
      MinerU
      文档结构解析
    图像处理
      Pillow
      img2pdf
      pypdf
    部署
      Docker Compose
      Nginx
      SQLite
```
