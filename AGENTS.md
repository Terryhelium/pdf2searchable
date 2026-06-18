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

- **后端**: Python 3.11+, FastAPI, uvicorn, aiosqlite, pypdf, Pillow, img2pdf, httpx
- **前端**: React 19, Ant Design 6, Vite 8, TypeScript 6, Axios
- **外部 OCR**: PaddleOCR (10.19.26.153:8080) + MinerU (10.19.26.153:8000)

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
