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
# 访问 http://<host>:9008
```

## 配置

关键环境变量见 `.env.example`。OCR 服务地址、超时、路径等全部通过环境变量控制，Docker 部署时在 docker-compose.yml 中覆盖 Docker 路径。
