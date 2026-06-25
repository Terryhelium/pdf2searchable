# PDF2Searchable

扫描版 PDF/图片 → 可搜索 PDF 的 Web 工具。前端 React + Ant Design 6，后端 FastAPI，Docker Compose 部署。

## 目录结构

```
.
├── backend/           FastAPI 后端
│   ├── app/
│   │   ├── main.py    路由入口
│   │   ├── config.py  环境变量配置（dataclass）
│   │   ├── db.py       SQLite 数据库（aiosqlite）
│   │   ├── models.py   Pydantic 响应模型
│   │   ├── ocr.py      PaddleOCR + MinerU 客户端
│   │   └── tasks.py    后台处理任务
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/          React + Vite 前端
│   ├── src/
│   │   ├── api/       axios API 客户端
│   │   ├── components/ 通用组件
│   │   └── pages/     页面组件
│   ├── Dockerfile + nginx.conf
│   └── package.json
├── docker-compose.yml
├── .env               本地/部署配置
└── todo.md            开发计划
```

## 依赖

- **后端**: Python 3.11+, FastAPI, uvicorn, aiosqlite, pypdf, Pillow, img2pdf, httpx, ocrmypdf, ocrmypdf-paddleocr
- **前端**: React 19, Ant Design 6, Vite 8, TypeScript 6, Axios
- **外部 OCR**: PaddleOCR-VL (10.19.26.153:8080) + MinerU (10.19.26.153:8000)
- **可搜索 PDF**: OCRmyPDF + PaddleOCR 插件（148 容器内 CPU / 153 GPU 服务待启用）

## 开发

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev

# 浏览器访问 http://localhost:5173
# WSL2 下 Windows 宿主机可用 localhost:5173
```

## 部署

```bash
docker compose up -d --build
# 访问 http://<host>:9010
```

## 配置

关键环境变量见 `.env.example`。OCR 服务地址、超时、路径等全部通过环境变量控制，Docker 部署时在 docker-compose.yml 中覆盖 Docker 路径。

## 当前交接备注

- 2026-06-19 已对双层 PDF 链路做了一轮保守修正，重点在 `backend/app/formatters/pdf.py`：
  - 增加旋转页坐标映射处理，针对 `/Rotate 90` / `/Rotate 270` 的扫描型 PDF。
  - 修正长文本块写入策略，避免 `insert_textbox()` 失败后静默丢字。
  - 增加 fallback 叠字日志，便于服务器环境复盘 `fitted/fallback` 块数。
- 已确认历史上确实试过两条双层 PDF 路线：
  - 路线A：直接在原 PDF 上叠隐藏文字层。
  - 路线B：先用 PyMuPDF 把原 PDF 渲染成 PNG，再以该 PNG 作为底图重建 PDF 后叠字。
- git 历史 `32db81e` 中保留过路线B实现：
  - `backend/app/ocr.py` 中曾按页 `get_pixmap()` 渲染 PNG 后发给 PaddleOCR。
  - `backend/app/formatters/pdf.py` 中曾新建 PDF 页面、插入渲染底图、再按 1:1 坐标叠字。
- 为了便于回退，保留了原文件备份：
  - `backend/app/formatters/pdf.py.bak`
  - `backend/app/tasks.py.bak`
- 单文件任务失败时，当前版本会把错误落到 `job_files.error_msg`，前端和数据库排障会更直接。
- 已将代表性 PDF 样本归档到 `cases/` 目录，桌面临时生成测试 PDF 已清理。

## 服务器优先验证样本

- 旋转扫描型异常样本：
  - `D:\SynologyDrive\临时方案\宁波市档案馆巡检项目\2026\宁波市档案馆终端安全管理系统采购项目\宁波市档案馆终端安全管理系统验收文档.pdf`
  - `D:\SynologyDrive\临时方案\宁波市档案馆巡检项目\2026\宁波市档案馆终端安全管理系统采购项目\14-2026_档案馆_终端安全管理_22000.pdf`
- 对照样本：
  - `D:\SynologyDrive\临时方案\宁波市档案馆巡检项目\2025\硬盘签收单（易拓 4T SATA 20251229）.pdf`

## 已确认的样本特征

- 上述两份 2026 验收类 PDF 都是“横向底图 + PDF 旋转元数据扶正显示”的类型：
  - `MediaBox` 为横向 A4。
  - 页面带 `/Rotate 90` 或 `/Rotate 270`。
  - 无原生文本层。
- 2025 签收单不是同类样本：
  - `Rotate = 0`
  - 能直接提取文本层
  - 更像拍照/电子来源 PDF，而不是纯扫描图 PDF
- 电子发票 `D:\SynologyDrive\My Documents\My Work\电子发票\2026\长春龙嘉-宁波栎社_20260504_1050.pdf`：
  - `Rotate = 0`
  - 可直接提取文本层（约 479 字符）
  - 属于电子 PDF，不适合作为扫描件双层 PDF 对齐问题的主测试样本

## 项目内案例集

- 已归档目录：`cases/`
- 说明文件：`cases/README.md`
- 作用：
  - 后续服务器环境复现时直接使用项目内案例，不再依赖桌面临时文件
  - 保留“原始异常样本 / 历史较好版 / 历史失败版 / 电子 PDF 参照”四类对照

## 桌面测试文件复盘

- `验收文档_可搜索版.pdf`
  - 3 页，`Rotate = 90`
  - 提取字符分布：`1006 / 0 / 623`
- `验收文档_最终版.pdf`
  - 3 页，`Rotate = 90`
  - 提取字符分布：`1006 / 0 / 623`
- `验收文档_对齐版.pdf`
  - 3 页，`Rotate = 90`
  - 提取字符分布：`1006 / 0 / 0`
  - 说明不仅存在高亮错位，也存在页级文字层缺失
- `验收文档_完美版.pdf`
  - 3 页，`Rotate = 0`
  - 提取字符分布：`1000 / 822 / 617`
  - 是桌面几版里最接近正确结果的一版，值得在服务器环境重点追溯其生成方式

## 当前路线判断

- 从成品质量看，主路线应优先选择“原 PDF 上叠隐藏文字层”，这是更正统也更保真的做法。
- “先重渲染再叠字”更适合作为特殊扫描型 PDF 的补救或实验路线，不建议作为所有 PDF 的默认策略。
- 对“横向底图 + `/Rotate` + 无文本层”的扫描件，后续更适合走特判流程，而不是对所有 PDF 一刀切重渲染。

## 服务器到位后建议顺序

1. 先只测试 PDF 输出，不要同时勾选太多格式。
2. 优先跑两份旋转型异常样本，观察搜索高亮位置是否回正。
3. 查看后端日志中的 `blocks / fitted / fallback` 统计。
4. 对照桌面 `验收文档_完美版.pdf` 的行为，判断当时是否使用了“先转正 / 先重建页面”的路线。
5. 若仍异常，再抓 Paddle 原始返回中的 `prunedResult.width/height`、`block_bbox` 与实际页尺寸做对照。

## 2026-06-22 最新交接

- 生产环境：
  - 应用服务器：`10.19.26.148`
  - OCR 服务器：`10.19.26.153`
  - 项目目录：`/opt/pdf2searchable-v2`
- 生产容器：
  - `pdf2searchable-backend`
  - `pdf2searchable-nginx`
- 这次只动过 `pdf2searchable` 自己的前端 / nginx / backend，不要碰 OCR 服务器其它服务。

### 当前前端状态

- UI 已做过一轮大改并已部署过生产。
- 主题切换仍有问题：
  - 用户反馈右上角主题控件在生产环境下仍不稳定。
  - 当前怀疑点是 Antd 主题切换和自定义 CSS 变量切换没有完全同步。
- 左上角品牌名不应再使用 `PDF2Searchable`。
- 下次建议直接改成：
  - 主名称：`档案数字化平台`
  - 副标题：`OCR · 转换 · 校核`

### 当前 PDF 重点问题

- 问题样本：
  - 源文件：`14-2026_档案馆_终端安全管理_22000.pdf`
  - 生成文件：`4834c41d50094fd3b22172d931443fce_14-2026_档案馆_终端安全管理_22000_searchable.pdf`
- 生产卷路径已确认：
  - 源文件：`/var/lib/docker/volumes/pdf2searchable-v2_uploads/_data/4834c41d50094fd3b22172d931443fce_14-2026_档案馆_终端安全管理_22000.pdf`
  - 输出文件：`/var/lib/docker/volumes/pdf2searchable-v2_uploads/_data/results/pdf/4834c41d50094fd3b22172d931443fce_14-2026_档案馆_终端安全管理_22000_searchable.pdf`
- 已确认：
  - 源 PDF 三页全部 `Rotate = 90`
  - 源 PDF 无原生文字层
  - 输出 PDF 三页仍保持 `Rotate = 90`
  - 输出 PDF 文字层存在：
    - page1 `1138`
    - page2 `1017`
    - page3 `849`
- 已抓到 Paddle 第 1 页原始块框，框本身大体合理：
  - `doc_title [391, 159, 828, 203] 终端安全管理系统采购合同`
  - `table [171, 600, 1039, 1278] ...`
- 当前更强的判断：
  - 问题不再像“Paddle 坐标完全错了”
  - 更像“在仍然带 `/Rotate=90` 的扫描页上直接按块叠字，导致搜索高亮和实际显示不完全贴合”

### 下次优先实现

在 `backend/app/formatters/pdf.py` 做窄范围特判：

1. 只对 `rotation in {90, 270}` 且无原生文字层的扫描页生效。
2. 先把页面转正重建为 `Rotate = 0` 的输出页。
3. 再按转正后的坐标叠加隐藏文字层。
4. 正常 PDF 继续走当前“原 PDF 上叠字”的主路线。

## 2026-06-25 最新交接

### 可搜索PDF坐标对齐问题 — 已解决

采用 **OCRmyPDF + PaddleOCR 插件**方案，搜索高亮偏移问题已修复。

关键文件：
- `backend/app/formatters/pdf.py` — 调用 OCRmyPDF 处理 PDF 格式
- `backend/app/ocr.py` — PDF 格式不调用远程 PaddleOCR API（由 OCRmyPDF 内部处理）
- `ocrmypdf-gpu-service/` — 153 GPU 服务的 Dockerfile 和 HTTP 服务代码
- `SEARCHABLE_PDF_ISSUE.md` — 完整技术分析文档

### 服务器状态

**148（应用服务器）**：
- `pdf2searchable-backend` — 已安装 ocrmypdf + ocrmypdf-paddleocr（CPU 版）
- `pdf2searchable-nginx` — 前端代理
- PDF 处理走本地 CPU OCRmyPDF（3 页约 2-3 分钟）

**153（算力服务器）**：
- `paddleocr-vl-api` + `paddleocr-vlm-server` — PaddleOCR-VL（:8080，用于 JSON 格式）
- `mineru-api` — MinerU（:8000，用于 TXT/MD 格式）
- `rerank-service` — RAG 服务
- `ocrmypdf-gpu` — OCRmyPDF GPU 服务（:8090，待修复 GPU 兼容性）

### GPU 加速待办

153 的 `ocrmypdf-gpu` 容器内执行：
```bash
pip install paddlepaddle-gpu==3.2.2 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
docker restart ocrmypdf-gpu
```

然后修改 148 `pdf.py` 调用 153 的 8090 端口。

### 下次进入会话第一步

1. 读 `todo.md` 和 `SEARCHABLE_PDF_ISSUE.md`
2. 在 153 容器内装 paddlepaddle-gpu 3.2.2（cu126）
3. 测试 GPU 处理速度
4. 改 148 后端调用 153 服务
