# 宁波市档案馆文档OCR处理系统

[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb)](https://react.dev/)
[![Ant Design](https://img.shields.io/badge/Ant%20Design-6-1677ff)](https://ant.design/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> 面向档案数字化的文档 OCR 处理系统。支持将扫描版 PDF / 图片转换为可搜索 PDF、TIFF 归档、JPEG 预览、纯文本、Markdown 及 JSON 结构化数据输出。

## 功能特性

- **多格式输出** — 一次处理同时生成 PDF / TIFF / JPEG / TXT / MD / JSON，按格式分目录存放
- **双引擎 OCR** — PaddleOCR（文字检测+精确坐标） + MinerU（文档结构解析）
- **仪表盘** — 处理统计概览、今日任务量、成功率
- **批量处理** — 指定源目录，后台逐文件处理
- **格式按需调用** — 仅对请求的格式调用对应的 OCR 引擎，TIFF/JPEG 无需 OCR
- **深色模式 + 主题色切换** — 6 种主题色预设
- **Docker 部署** — 一键启动，Nginx 反代 + 后端容器化

## 系统架构

```
┌──────────┐    ┌──────────────────────────────────────────────┐
│  Browser  │    │                  Nginx (:9008)               │
│  (React)  │───▶│  /api/* → backend:8000                       │
│          │    │  /*      → frontend static files              │
└──────────┘    └──────────────┬───────────────────────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │    FastAPI Backend       │
                    │  ┌────────────────────┐  │
                    │  │ OCRProcessor       │  │
                    │  │  ├─ PaddleOCR      │──▶── 10.19.26.153:8080
                    │  │  └─ MinerU         │──▶── 10.19.26.153:8000
                    │  ├─ Formatters        │  │
                    │  │  ├─ PDF / TIFF     │  │
                    │  │  ├─ JPEG / TXT    │  │
                    │  │  └─ MD / JSON     │  │
                    │  └─ SQLite Database  │  │
                    └──────────────────────┘  │
                    └─────────────────────────┘
```

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

## 输出目录结构

```
目标目录/
├── pdf/      → document_searchable.pdf   (可搜索PDF: 原图+文字层)
├── tiff/     → document.tiff             (归档级TIFF, LZW压缩)
├── jpg/      → document_p1.jpg           (JPEG预览, 每页一张)
├── txt/      → document.txt              (纯文本: 按阅读顺序)
├── md/       → document.md               (Markdown: 结构化输出)
└── json/     → document.json             (OCR完整数据, 供NER标注)
```

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 19, TypeScript 6, Ant Design 6, Vite 8 |
| 后端 | Python 3.11+, FastAPI, uvicorn, aiosqlite |
| OCR | PaddleOCR + MinerU (独立HTTP服务) |
| 图像 | Pillow, img2pdf, pypdf |
| 部署 | Docker Compose, Nginx |
