# 系统架构

## 整体架构

```mermaid
graph TB
    subgraph Client["🧑 用户端"]
        WB["Windows 浏览器<br/>localhost:5173"]
    end

    subgraph NginxLayer["🌐 Nginx 反向代理 (:9008)"]
        direction LR
        SPA["前端静态资源<br/>→ /usr/share/nginx/html"]
        API["API 代理<br/>→ http://backend:8000"]
    end

    subgraph Backend["⚙️ FastAPI 后端 (:8000)"]
        Router["API 路由层<br/>/api/*"]
        Proc["OCRProcessor<br/>引擎调度 + 格式生成"]

        subgraph Engines["OCR 引擎客户端"]
            POClient["PaddleOCRClient"]
            MUClient["MinerUClient"]
        end

        subgraph Formatters["格式输出器"]
            FPDF["PDFFormatter"]
            FTIFF["TIFFFormatter"]
            FJPG["JPEGFormatter"]
            FTXT["TextFormatter"]
            FMD["MarkdownFormatter"]
            FJSON["JSONFormatter"]
        end

        Database[("SQLite<br/>jobs.db")]
        Tasks["Tasks<br/>后台任务调度"]
    end

    subgraph OcrServers["🖥️ OCR 算力服务器 (10.19.26.153)"]
        PO["PaddleOCR<br/>:8080"]
        MU["MinerU<br/>:8000"]
    end

    subgraph Storage["💾 持久化存储"]
        DBFile[("data/jobs.db")]
        Uploads[("uploads/ 临时文件")]
        Results[("目标目录/ 输出结果")]
    end

    WB -->|"HTTP"| NginxLayer
    NginxLayer -->|"/api/*"| Router
    WB -->|"开发模式 :5173 直连"| Router

    Router --> Proc
    Router --> Tasks
    Router <--> Database

    Proc --> POClient
    Proc --> MUClient
    POClient -->|"HTTP POST /ocr"| PO
    MUClient -->|"HTTP POST /api/v1/parse"| MU

    Proc --> FPDF
    Proc --> FTIFF
    Proc --> FJPG
    Proc --> FTXT
    Proc --> FMD
    Proc --> FJSON

    Database --> DBFile
    Proc --> Uploads
    Formatters --> Results

    classDef client fill:#e3f2fd,stroke:#1565c0,color:#1565c0
    classDef nginx fill:#fff3e0,stroke:#e65100,color:#e65100
    classDef backend fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32
    classDef engine fill:#fce4ec,stroke:#c62828,color:#c62828
    classDef format fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32
    classDef ocr fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a
    classDef storage fill:#f5f5f5,stroke:#616161,color:#616161

    class WB client
    class NginxLayer,SPA,API nginx
    class Router,Proc,Tasks,Database backend
    class POClient,MUClient engine
    class FPDF,FTIFF,FJPG,FTXT,FMD,FJSON format
    class PO,MU ocr
    class DBFile,Uploads,Results storage
```

---

## 处理流水线

```mermaid
flowchart TB
    Start(["📄 用户上传文件<br/>或指定批量目录"]) --> CreateJob["创建 Job 记录<br/>写入 SQLite"]

    CreateJob --> EngineSelect{"按需选择 OCR 引擎"}

    EngineSelect -->|"格式包含 PDF"| PO_OCR["PaddleOCR<br/>返回: 文字 + 坐标 + 置信度"]
    EngineSelect -->|"格式包含 MD/TXT"| MU_OCR["MinerU<br/>返回: 标题/表格/阅读顺序"]
    EngineSelect -->|"格式包含 JSON"| Both["PaddleOCR + MinerU"]
    EngineSelect -->|"仅 TIFF/JPEG"| NoOCR["不调用 OCR<br/>直接图像处理"]

    PO_OCR --> Merge["合并 OCR 结果"]
    MU_OCR --> Merge
    Both --> Merge
    NoOCR --> Merge

    Merge --> MultiFormat{"逐个格式生成"}

    subgraph FormatGen["格式生成"]
        direction TB
        F1["📕 PDFFormatter<br/>pypdf: 原图 + 文字覆盖层"]
        F2["🖼️ TIFFFormatter<br/>Pillow: 多页 TIFF + LZW"]
        F3["🖼️ JPEGFormatter<br/>Pillow: 逐页 JPEG 预览"]
        F4["📃 TextFormatter<br/>按阅读顺序拼接纯文本"]
        F5["📝 MarkdownFormatter<br/>MinerU 结构 → Markdown 语法"]
        F6["📊 JSONFormatter<br/>完整数据 + 版式信息"]
    end

    MultiFormat -->|PDF| F1
    MultiFormat -->|TIFF| F2
    MultiFormat -->|JPEG| F3
    MultiFormat -->|TXT| F4
    MultiFormat -->|MD| F5
    MultiFormat -->|JSON| F6

    F1 & F2 & F3 & F4 & F5 & F6 --> OutDir["写入对应格式子目录<br/>pdf/ tiff/ jpg/ txt/ md/ json/"]

    OutDir --> UpdateStatus["更新 Job 状态 → done"]
    UpdateStatus --> Done(["✅ 处理完成"])

    classDef start fill:#e3f2fd,stroke:#1565c0,color:#1565c0
    classDef process fill:#fff3e0,stroke:#e65100,color:#e65100
    classDef engine fill:#fce4ec,stroke:#c62828,color:#c62828
    classDef format fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32
    classDef output fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a
    classDef end fill:#e8f5e9,stroke:#1b5e20,color:#1b5e20

    class Start start
    class CreateJob,EngineSelect,Merge,MultiFormat,NoOCR process
    class PO_OCR,MU_OCR,Both engine
    class F1,F2,F3,F4,F5,F6 format
    class OutDir,UpdateStatus output
    class Done end
```

---

## 模块依赖关系

```mermaid
graph RL
    subgraph API["API 层"]
        Main["main.py<br/>路由 + 生命周期"]
    end

    subgraph Core["核心逻辑"]
        OCR["ocr.py<br/>OCRProcessor"]
        Tasks["tasks.py<br/>后台任务"]
        DB["db.py<br/>Database"]
    end

    subgraph Format["格式输出器"]
        Init["formatters/__init__.py<br/>BaseFormatter + Registry"]
        PDF["pdf.py<br/>SearchablePDFFormatter"]
        TIFF["tiff.py<br/>TIFFFormatter"]
        JPEG["jpeg.py<br/>JPEGFormatter"]
        TXT["txt.py<br/>TextFormatter"]
        MD["md.py<br/>MarkdownFormatter"]
        JSON["json.py<br/>JSONFormatter"]
    end

    subgraph Config["配置"]
        CFG["config.py<br/>Settings"]
        ENV[".env<br/>环境变量"]
    end

    subgraph Models["数据模型"]
        MOD["models.py<br/>Pydantic Models"]
    end

    Main --> OCR
    Main --> Tasks
    Main --> DB
    Main --> MOD
    Main --> CFG

    Tasks --> OCR
    Tasks --> DB

    OCR -->|"按需调用"| Init
    Init --> PDF
    Init --> TIFF
    Init --> JPEG
    Init --> TXT
    Init --> MD
    Init --> JSON

    DB --> CFG
    OCR --> CFG

    classDef api fill:#e3f2fd,stroke:#1565c0,color:#1565c0
    classDef core fill:#fff3e0,stroke:#e65100,color:#e65100
    classDef fmt fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32
    classDef cfg fill:#f5f5f5,stroke:#616161,color:#616161
    classDef mod fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a

    class Main api
    class OCR,Tasks,DB core
    class Init,PDF,TIFF,JPEG,TXT,MD,JSON fmt
    class CFG,ENV cfg
    class MOD mod
```

---

## 数据库模型

```mermaid
erDiagram
    jobs {
        str id PK "UUID"
        str type "single | batch"
        str status "pending | processing | done | failed"
        str source_dir "批量源目录"
        str dest_dir "批量目标目录"
        int total_files "文件总数"
        int processed_files "已处理数"
        int error_count "错误数"
        str formats "pdf,tiff,jpg,txt,md,json"
        str created_at "ISO 时间戳"
        str updated_at "ISO 时间戳"
    }

    job_files {
        int id PK "自增"
        str job_id FK "关联 jobs.id"
        str filename "原始文件名"
        str status "pending | done | failed"
        str error_msg "错误信息"
        str result_path "主输出文件路径"
    }

    jobs ||--o{ job_files : contains
```

---

## 输出目录结构

```mermaid
graph TB
    Dest["📂 目标目录"] --> pdf["📂 pdf/"]
    Dest --> tiff["📂 tiff/"]
    Dest --> jpg["📂 jpg/"]
    Dest --> txt["📂 txt/"]
    Dest --> md["📂 md/"]
    Dest --> json["📂 json/"]

    pdf --> p1["📕 doc1_searchable.pdf"]
    pdf --> p2["📕 doc2_searchable.pdf"]

    tiff --> t1["🖼️ doc1.tiff"]
    tiff --> t2["🖼️ doc2.tiff"]

    jpg --> j1["🖼️ doc1_p1.jpg"]
    jpg --> j2["🖼️ doc1_p2.jpg"]
    jpg --> j3["🖼️ doc2_p1.jpg"]

    txt --> x1["📃 doc1.txt"]
    txt --> x2["📃 doc2.txt"]

    md --> m1["📝 doc1.md"]
    md --> m2["📝 doc2.md"]

    json --> s1["📊 doc1.json"]
    json --> s2["📊 doc2.json"]

    classDef root fill:#fff3e0,stroke:#e65100,color:#e65100
    classDef dir fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32
    classDef file fill:#f5f5f5,stroke:#9e9e9e,color:#616161

    class Dest root
    class pdf,tiff,jpg,txt,md,json dir
    class p1,p2,t1,t2,j1,j2,j3,x1,x2,m1,m2,s1,s2 file
```

---

## 前端组件树

```mermaid
graph TB
    App["App.tsx<br/>ConfigProvider + 主题管理"] --> Layout["AppLayout.tsx<br/>侧边栏 + 顶栏"]
    Layout --> Nav["Sider<br/>导航菜单"]
    Layout --> Header["Header<br/>折叠按钮 + 主题色 + 暗色切换"]

    Layout --> Dashboard["Dashboard.tsx<br/>仪表盘"]
    Layout --> Upload["SingleUpload.tsx<br/>单文件上传"]
    Layout --> Batch["BatchProcess.tsx<br/>批量处理"]

    Upload --> FormatSel["FormatSelector<br/>输出格式选择"]
    Upload --> Zone["UploadZone<br/>拖拽上传"]
    Upload --> Jobs["JobList<br/>任务记录"]

    Batch --> FormatSel
    Batch --> BForm["Form<br/>源/目标目录"]
    Batch --> BList["List<br/>任务列表"]
    Batch --> Detail["JobDetail<br/>任务详情 Modal"]

    classDef app fill:#e3f2fd,stroke:#1565c0,color:#1565c0
    classDef layout fill:#fff3e0,stroke:#e65100,color:#e65100
    classDef page fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32
    classDef comp fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a

    class App app
    class Layout,Nav,Header layout
    class Dashboard,Upload,Batch page
    class FormatSel,Zone,Jobs,BForm,BList,Detail comp
```
