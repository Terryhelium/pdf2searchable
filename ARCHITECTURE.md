# 系统架构

## 整体架构

宁波市档案馆文档OCR处理系统采用前后端分离架构，前端通过 Nginx 反代与后端通信。外部 OCR 服务（PaddleOCR、MinerU）通过 HTTP 调用。

```
┌─────────┐     ┌──────────────────────────────────────────────────┐
│ Windows  │     │               Docker / Local                     │
│ Browser  │     │                                                   │
│ :5173    │────▶│  Nginx (:9008)  ──proxy──▶  FastAPI (:8000)      │
│ :9008    │     │       │                           │              │
└─────────┘     │       │                    ┌───────▼───────┐      │
                │       │                    │  SQLite       │      │
                │       │                    │  (jobs.db)    │      │
                │       │                    └───────────────┘      │
                │       │                           │              │
                │       │                    ┌───────▼───────┐      │
                │       │                    │  OCRProcessor │      │
                │       │                    │               │      │
                │       │            ┌───────▼───┐  ┌───────▼───┐  │
                │       │            │ PaddleOCR │  │  MinerU   │  │
                │       │            │ :8080     │  │  :8000    │  │
                │       │            └───────────┘  └───────────┘  │
                │       │                           │              │
                │       │                    ┌───────▼───────┐      │
                │       │                    │  Formatters   │      │
                │       │                    │ PDF/TIFF/JPEG │      │
                │       │                    │ TXT/MD/JSON   │      │
                │       │                    └───────────────┘      │
                └───────┴───────────────────────────────────────────┘
```

## 后端模块

### app/main.py
FastAPI 应用入口，注册路由和生命周期（数据库连接、OCR 客户端初始化）。

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查（含OCR引擎状态） |
| `/api/stats` | GET | 处理统计数据 |
| `/api/upload` | POST | 单文件上传处理 |
| `/api/jobs/{id}` | GET | 查询任务状态 |
| `/api/download/{id}/{file}` | GET | 下载处理结果 |
| `/api/batch` | POST | 创建批量处理任务 |
| `/api/batch` | GET | 批量任务列表 |
| `/api/batch/{id}` | GET | 批量任务详情 |

### app/ocr.py
OCR 引擎客户端 + 处理器。

- **PaddleOCRClient**: 调用 PaddleOCR HTTP API，返回文字检测结果（文本 + 坐标 + 置信度）
- **MinerUClient**: 调用 MinerU HTTP API，返回文档结构解析结果（标题、表格、阅读顺序）
- **OCRProcessor**: 协调引擎调用和格式输出，按需只调用必要的引擎：
  - `pdf` → PaddleOCR（需要精确文字坐标做覆盖层）
  - `md` / `txt` → MinerU（需要文档结构理解）
  - `json` → 两个都调
  - `tiff` / `jpeg` → 都不调（纯图像转换）

### app/formatters/
每个输出格式是一个独立的 Formatter，通过注册表自动发现：

```
formatters/
├── __init__.py    # BaseFormatter 基类 + 注册表
├── pdf.py         # 可搜索PDF（原图 + pypdf 覆盖文字层）
├── tiff.py        # 归档TIFF（LZW 压缩）
├── jpeg.py        # JPEG 预览图（每页一张）
├── txt.py         # 纯文本提取
├── md.py          # Markdown 结构化输出
└── json.py        # JSON 完整数据导出
```

### app/db.py
SQLite 数据库封装（aiosqlite），表结构：

```sql
jobs          -- 任务主表（id, type, status, formats, stats...）
job_files     -- 任务文件明细（filename, status, error_msg, result_path）
```

### app/tasks.py
后台任务处理：
- `process_single_file()` — 单文件上传处理
- `run_batch_job()` — 批量目录处理，逐文件 OCR + 格式化

## 前端模块

### 页面

| 路径 | 组件 | 说明 |
|------|------|------|
| 仪表盘 | Dashboard | 统计卡片 + 最近处理记录 |
| 上传 | SingleUpload | 文件上传 + 格式选择 + 状态跟踪 |
| 批量 | BatchProcess | 批量任务创建 + 任务列表 + 详情 |

### 组件

| 组件 | 说明 |
|------|------|
| AppLayout | 侧边栏导航 + 顶栏（主题切换） |
| UploadZone | 拖拽上传区域 |
| FormatSelector | 输出格式多选框 |
| JobList | 任务列表 |
| JobDetail | 任务详情（含文件级进度） |

### 状态管理

- 主题模式（ConfigProvider）
- 页面路由（状态驱动，无 router 依赖）
- 任务状态轮询（useRef 定时器）

## 处理流程

```
输入文件
  │
  ├── 格式判断
  │   ├── pdf/md/txt/json → 调用对应 OCR 引擎
  │   └── tiff/jpeg       → 跳过 OCR，直接做图像转换
  │
  ├──→ 输出目录
  │     ├── pdf/     → SearchablePDFFormatter
  │     ├── tiff/    → TIFFFormatter
  │     ├── jpg/     → JPEGFormatter（每页）
  │     ├── txt/     → TextFormatter
  │     ├── md/      → MarkdownFormatter
  │     └── json/    → JSONFormatter
  │
  └──→ 数据库记录更新
```

## 部署架构

生产环境通过 Docker Compose 部署：

- **backend**: FastAPI 应用容器
- **nginx**: 前端静态资源 + API 反代

外部依赖：
- **PaddleOCR** 服务（10.19.26.153:8080）
- **MinerU** 服务（10.19.26.153:8000）
