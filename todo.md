# 宁波市档案馆文档OCR处理系统 开发日志

## ✅ 已完成（2026-06-11 ~ 06-13）

### 框架搭建
- [x] 依赖全部升级至最新：antd 6 / vite 8 / TS 6 / FastAPI 0.136
- [x] PyPDF2 → pypdf 迁移，后端全部包 latest
- [x] 前后端分离架构，FastAPI + React + Ant Design 6

### 界面
- [x] 侧边导航栏（仪表盘 / 上传 / 批量）
- [x] 仪表盘页面：6 个统计卡片 + 最近处理记录
- [x] 单文件上传页：拖拽上传 + 格式选择 + 状态轮询 + 结果下载
- [x] 批量处理页：目录输入 + 格式选择 + 任务列表 + 文件级详情
- [x] 深色/浅色模式切换 + 6 种主题色预设

### 后端
- [x] API 路由：health / stats / upload / batch / download / job query
- [x] SQLite 数据库（aiosqlite），jobs + job_files 表
- [x] PaddleOCR + MinerU HTTP 客户端骨架
- [x] Formatter 架构：6 种格式独立模块 + 注册表自动发现
- [x] OCR 引擎按需调用（TIFF/JPEG 不需要 OCR）
- [x] 输出按格式分目录：pdf/ tiff/ jpg/ txt/ md/ json/
- [x] 统计接口 /api/stats
- [x] JSON 格式输出（完整 OCR 数据，预留 NER 标注）

### 工程
- [x] Docker Compose 部署配置
- [x] .gitignore / .editorconfig / CLAUDE.md
- [x] README.md + ARCHITECTURE.md（Mermaid 彩图 x 8）
- [x] CHANGELOG.md / ROADMAP.md / CONTRIBUTING.md
- [x] GIT_REMOTE.md + 双远程推送（Gitea + GitHub）

---

## ⏳ 待办（按优先级）

### 一、连上 OCR 服务器后
- [ ] 验证 PaddleOCR 真实 API 格式，修正客户端
- [ ] 验证 MinerU 真实 API 格式，修正客户端
- [ ] 实现 SearchablePDFFormatter（pypdf 叠加文字层）
- [ ] 实现 TIFFFormatter（Pillow 多页 TIFF + LZW）
- [ ] 实现 JPEGFormatter（Pillow 逐页预览图）
- [ ] 实现 TextFormatter（按 MinerU 阅读顺序提取）
- [ ] 实现 MarkdownFormatter（MinerU 结构转 MD 语法）
- [ ] 端到端单文件 + 批量流程测试
- [ ] docker compose up 完整部署验证

### 二、上线准备
- [ ] NAS 挂载路径配置
- [ ] Docker 镜像瘦身
- [ ] USER_MANUAL.md 用户操作手册
- [ ] 部署文档
