# 更新日志

## [2.1.0] - 2026-06-25

### 重大变更
- 可搜索 PDF 生成引擎：自研方案 → OCRmyPDF + PaddleOCR 插件
- 坐标对齐：旋转扫描件搜索高亮偏移问题彻底解决
- PDF 格式不再调用远程 PaddleOCR API，由 OCRmyPDF 内部处理

### 新增
- OCRmyPDF + PaddleOCR 插件集成（坐标对齐有保障）
- 153 GPU 服务：`ocrmypdf-gpu` 容器（端口 8090）
- PaddlePaddle 3.2.2 GPU（CUDA 12.6）支持
- `SEARCHABLE_PDF_ISSUE.md` 技术分析文档

### 技术细节
- OCRmyPDF 负责坐标对齐（同一张渲染图做 OCR 和底图）
- PaddleOCR 负责中文识别质量
- 旋转页面自动处理，输出 rotation=0
- 153 容器：Python 3.11 + OCRmyPDF 17.7.0 + PaddleOCR 3.7.0 + PaddlePaddle GPU 3.2.2

### 性能
- CPU 版（148 容器内）：3 页 PDF 约 2-3 分钟
- GPU 版（153 服务）：3 页 PDF 约 50 秒（含 rotate-pages + deskew）

## [2.0.0] - 2026-06-18

### 重大变更
- 架构升级：旧版 `server.py`（单文件 systemd 服务）→ Docker Compose（FastAPI + React）
- 端口变更：9008 → 9010
- 旧版 systemd 服务已停用

### 新增
- 6 种输出格式：可搜索 PDF / TIFF 归档 / JPEG 预览 / 纯文本 / Markdown / JSON
- MinerU 文档解析引擎集成（代替纯 PaddleOCR 方案）
- 双引擎按需路由：PDF→PaddleOCR，MD/TXT→MinerU，JSON→两个引擎
- 前端 React 19 + Ant Design 6 SPA
- 仪表盘页面（统计概览 + 最近处理记录）
- 批量处理：支持服务器目录和本地上传两种模式
- 目录浏览 API + 前端目录选择器
- 任务记录管理：详情查看、格式下载、单删、批量删除
- 同步处理模式（上传直等待返回，无需轮询）
- 深色/浅色模式切换 + 6 种主题色预设
- 取消按钮 + 处理耗时显示

### 修复
- OCR API 路径修正：PaddleOCR `/ocr` → `/layout-parsing`（base64 JSON）
- MinerU `/api/v1/parse` → `/file_parse`（multipart 上传）
- Nginx proxy 超时从 300s 加到 600s
- OCR 超时从 120s 加到 600s
- Dockerfile 包名修正：`libgl1-mesa-glx` → `libgl1`
- Formatter 模块未注册导致"未知格式"的 Bug
- `formats` 参数未传递到 `process_single_file` 的 Bug
- 下载链接 URL 格式不匹配的 Bug
- Markdown LaTeX 公式标记乱码清理
- Dockerfile 添加阿里云 apt 镜像加速

## [0.2.0] - 2026-06-12

### 新增
- 多格式输出框架（PDF / TIFF / JPEG / TXT / MD / JSON）
- 输出格式选择器
- 仪表盘页面
- 侧边导航栏
- 深色/浅色模式切换
- 6 种主题色预设
- Formatter 架构：每个格式独立模块 + 注册表
- OCR 引擎按需调用
- 统计接口 `/api/stats`
- JSON 格式输出

### 变更
- 项目更名：宁波市档案馆文档OCR处理系统
- 前端框架升级：antd 5→6, vite 6→8, TypeScript 5→6
- 后端依赖升级：FastAPI 0.115→0.136, PyPDF2→pypdf
- 输出目录改按格式分目录

## [0.1.0] - 2026-06

### 初始版本
- FastAPI 后端骨架
- React 前端基础页面
- Docker Compose 部署配置
- PaddleOCR + MinerU HTTP 客户端占位
