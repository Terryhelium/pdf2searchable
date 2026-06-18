# AI 服务资源调度指南

## 服务器概览

| 服务器 | 主机名 | IP | 角色 | GPU | 内存 |
|--------|--------|-----|------|-----|------|
| 153 | ai-compute | 10.19.26.153 | 算力服务器 | Tesla T4 15GB | 32GB |
| 148 | ai-app | 10.19.26.148 | 应用服务器 | 无 | 32GB |

## 服务列表

### 153 算力服务器（有 GPU）

| 服务 | 用途 | 端口 | GPU 占用 | 启动目录 |
|------|------|------|----------|----------|
| PaddleOCR-VL | OCR 文字识别 | 8080 | ~9.5 GB | `/opt/paddleocr-vl/` |
| MinerU | 文档解析 | 8000, 7860 | ~2.2 GB | `/opt/mineru-server/` |
| Rerank Service | RAG 搜索重排序 | 7997 | ~2 GB | `/opt/rerank-service/` |
| FunASR | 语音识别 (ASR) | 10096 | **无** (CPU) | `/opt/funasr/` |
| CosyVoice | 语音合成 (TTS) | 50000 | ~4 GB | `/opt/cosyvoice/` |
| MetaHuman | 数字人流媒体 | 8001, 8010 | ~6 GB | `/opt/metahuman-stream/` |
| Ollama | LLM 大模型推理 | 11434 | 取决于模型 | systemd 服务 |

### 148 应用服务器（无 GPU）

| 服务 | 用途 | 端口 | 启动目录 |
|------|------|------|----------|
| Fay | 数字人交互 | 5000, 5443 | `/docker/fay/` |
| RAGFlow | RAG 知识库检索 | 19001-19004 | `/opt/ragflow-deploy/docker/` |
| OpenWebUI | AI 对话界面 | 3000 | `/opt/open-webui/` |
| OpenWebUI-Public | AI 对话（公开版） | 3001 | `/opt/openwebui-rag-proxy/` |
| Reception Kiosk | 接待终端 | 18080 | `/opt/reception-kiosk/` |
| Dify | 工作流平台 | 80, 443 | `/opt/dify/docker/` |
| N8N | 自动化工作流 | 5678 | `/opt/n8n-ai-ops/` |
| **PDF2Searchable v2** | **OCR 双层 PDF** | **9010** | **`/opt/pdf2searchable-v2/`**（Docker） |
| Label Studio | 数据标注 | 8080, 9090 | — |
| Doc-Parser | 文档解析 | 8501, 8502 | — |

> PDF2Searchable 旧版 (systemd, 9008) 已停用，由新版 Docker 版 (9010) 替代。

---

## GPU 资源冲突说明

153 服务器只有一张 **Tesla T4 (15GB)** 显存。

| 服务组合 | GPU 需求 | 能否同时运行 |
|----------|----------|-------------|
| 仅 PaddleOCR | ~9.5 GB | 可以 |
| 仅 MinerU | ~2.2 GB | 可以 |
| 仅 Ollama (7B 模型) | ~5 GB | 可以 |
| 仅 CosyVoice | ~4 GB | 可以 |
| 仅 MetaHuman | ~6 GB | 可以 |
| PaddleOCR + MinerU | ~11.7 GB | ✅ 可以（当前 OCR 场景） |
| Ollama + Rerank | ~7 GB | 可以 |
| PaddleOCR + FunASR | ~9.5 GB | 可以 (FunASR 不用 GPU) |
| Ollama + MetaHuman + CosyVoice | ~15 GB | 勉强可以（数字人全栈） |
| PaddleOCR + Ollama | ~14.5 GB | 勉强，可能 OOM |
| 以上任意三个 GPU 服务 | >15 GB | **不行** |

---

## 应用场景与资源调度

### 场景一：使用数字人

**需要的 153 服务：** Ollama + FunASR + CosyVoice + MetaHuman
**需要关闭的 153 服务：** PaddleOCR、MinerU、Rerank Service
**需要的 148 服务：** Fay + Reception Kiosk

```
153 停掉: PaddleOCR, MinerU, Rerank
153 启动: Ollama, CosyVoice, MetaHuman (FunASR 常驻不动)
148 启动: Fay, Reception Kiosk
```

### 场景二：使用 RAG 知识库 / OpenWebUI 对话

**需要的 153 服务：** Ollama + Rerank Service
**需要关闭的 153 服务：** PaddleOCR、MinerU、CosyVoice、MetaHuman
**需要的 148 服务：** RAGFlow + OpenWebUI (+ 可选 Dify)

```
153 停掉: PaddleOCR, MinerU, CosyVoice, MetaHuman
153 启动: Ollama, Rerank (FunASR 常驻不动)
148 启动: RAGFlow, OpenWebUI
```

### 场景三：使用 OCR 文档识别 / PDF 双层化

**需要的 153 服务：** PaddleOCR + MinerU
**需要关闭的 153 服务：** Ollama、Rerank、CosyVoice、MetaHuman
**需要的 148 服务：** PDF2Searchable v2（上传 PDF/图片生成可搜索 PDF 等多格式输出）

**访问地址：** http://10.19.26.148:9010

```
153 停掉: Ollama, Rerank, CosyVoice, MetaHuman
153 启动: PaddleOCR, MinerU (FunASR 常驻不动)
148 启动: PDF2Searchable v2 (Docker)
```

> 支持上传 PDF、PNG、JPG、TIFF、BMP，输出可选 6 种格式：可搜索 PDF / TIFF / JPEG / TXT / MD / JSON。

### 场景四：使用 Dify 工作流

Dify 运行在 148，不依赖 153 的 GPU 服务。可以和其他场景并行使用。

```
148 启动: Dify (始终可用)
```

---

## 服务开关速查

### 153 算力服务器

```bash
# SSH 连接
ssh root@10.19.26.153

# ---- Ollama (LLM) ----
sudo systemctl start ollama
sudo systemctl stop ollama
sudo systemctl status ollama

# ---- PaddleOCR (OCR) ----
cd /opt/paddleocr-vl && docker compose up -d     # 启动
cd /opt/paddleocr-vl && docker compose stop       # 停止（保留容器）
cd /opt/paddleocr-vl && docker compose start      # 再次启动
cd /opt/paddleocr-vl && docker compose ps -a      # 查看状态（含已停止）

# ---- MinerU (文档解析) ----
cd /opt/mineru-server && docker compose --profile api --profile gradio up -d
cd /opt/mineru-server && docker compose stop
cd /opt/mineru-server && docker compose start

# ---- Rerank Service ----
cd /opt/rerank-service && docker compose up -d
cd /opt/rerank-service && docker compose stop

# ---- FunASR (语音识别, CPU, 常驻) ----
cd /opt/funasr && docker compose up -d
cd /opt/funasr && docker compose down    # FunASR 用 down 没关系，常驻不常用

# ---- CosyVoice (TTS) ----
cd /opt/cosyvoice && docker compose up -d
cd /opt/cosyvoice && docker compose stop

# ---- MetaHuman (数字人流媒体) ----
cd /opt/metahuman-stream && docker compose up -d
cd /opt/metahuman-stream && docker compose stop
```

### 148 应用服务器

```bash
# SSH 连接
ssh root@10.19.26.148

# ---- Fay (数字人) ----
cd /docker/fay && docker compose up -d
cd /docker/fay && docker compose stop

# ---- RAGFlow ----
cd /opt/ragflow-deploy/docker && docker compose up -d
cd /opt/ragflow-deploy/docker && docker compose stop

# ---- OpenWebUI ----
cd /opt/open-webui && docker compose up -d
cd /opt/open-webui && docker compose stop

# ---- Reception Kiosk ----
cd /opt/reception-kiosk && docker compose -f docker-compose.kiosk.yml up -d
cd /opt/reception-kiosk && docker compose -f docker-compose.kiosk.yml stop

# ---- Dify ----
cd /opt/dify/docker && docker compose up -d
cd /opt/dify/docker && docker compose stop

# ---- N8N ----
cd /opt/n8n-ai-ops && docker compose up -d
cd /opt/n8n-ai-ops && docker compose stop

# ---- PDF2Searchable v2 (Docker, 9010) ----
cd /opt/pdf2searchable-v2 && docker compose up -d
cd /opt/pdf2searchable-v2 && docker compose stop
cd /opt/pdf2searchable-v2 && docker compose start
cd /opt/pdf2searchable-v2 && docker compose logs -f
```

---

## 数据持久性说明

所有服务的关键数据都保存在 Docker 命名卷 (named volumes) 中，**不受容器启停影响**：

| 服务 | 数据位置 | 存储内容 |
|------|---------|---------|
| PDF2Searchable v2 | `uploads` 卷 | 上传文件和转换结果 |
| PDF2Searchable v2 | `data` 卷 | SQLite 数据库（任务记录） |
| RAGFlow | 多个命名卷 | 知识库、向量数据 |
| MinIO | 命名卷 | 对象存储 |

> 只有 `docker compose down -v`（带 `-v` 参数）才会删除卷和数据。普通 `down`、`stop`、`start`、`restart` **不会影响数据**。

---

## 快速检查命令

```bash
# 查看 153 GPU 使用情况
ssh root@10.19.26.153 "nvidia-smi"

# 查看 153 所有容器（含已停止）
ssh root@10.19.26.153 "docker compose ps -a"

# 查看 148 所有容器
ssh root@10.19.26.148 "docker compose ps -a"
```

---

## 常见问题

**Q: Ollama 里有哪些模型？**
A: 已安装 deepseek-r1, qwen2.5, qwen2.5-coder, qwen3, qwen2.5vl, bge-m3, all-minilm, nomic-embed-text-long

**Q: FunASR 需要关吗？**
A: 不需要。FunASR 是 CPU 服务，不占 GPU，可以常驻。Fay 数字人依赖它做语音识别。

**Q: 148 上的服务会互相冲突吗？**
A: 148 没有 GPU，主要是内存和端口冲突。32GB 内存通常够用。如果内存紧张，可以关掉不用的服务。

**Q: 之前 PaddleOCR 容器怎么消失了？**
A: 旧版速查卡用的 `docker compose down`，这个命令会**删除容器**（不是 stop）。改成 `docker compose stop` 后，容器会保留，`docker compose ps -a` 能看到。

**Q: PDF2Searchable 的数据会丢吗？**
A: 不会。数据库和上传文件存在 Docker 命名卷里，`stop` 和 `down` 都不会删。上传记录永久保存在应用服务器上。
