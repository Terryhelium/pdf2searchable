# 更新日志

## [0.2.0] - 2026-06-12

### 新增
- 多格式输出：PDF / TIFF / JPEG / TXT / MD / JSON
- 输出格式选择器（前端 + 后端参数传递）
- 仪表盘页面（统计概览 + 最近记录）
- 侧边导航栏（仪表盘 / 上传 / 批量）
- 深色/浅色模式切换
- 6 种主题色预设（蓝/橙/黄/绿/紫/红）
- Formatter 架构：每个格式独立模块 + 注册表
- OCR 引擎按需调用（仅请求的格式需要的引擎）
- 统计接口 `/api/stats`
- JSON 格式输出（保留完整 OCR 数据，供 NER 标注）

### 变更
- 项目更名：宁波市档案馆文档OCR处理系统
- 前端框架升级：antd 5→6, vite 6→8, TypeScript 5→6
- 后端依赖升级：FastAPI 0.115→0.136, PyPDF2→pypdf
- 输出目录改按格式分目录（`pdf/`、`tiff/`、`jpg/`...）
- 默认路径改为本地相对路径（非 Docker 硬编码）

### 修复
- exception_handler 返回正确 HTTP 状态码（502）
- 单文件上传流程注册 job_files 表记录
- SQLite 统计查询 COALESCE 空值处理

## [0.1.0] - 2026-06

### 初始版本
- FastAPI 后端骨架（路由、数据库、OCR 客户端）
- React 前端基础页面
- Docker Compose 部署配置
- PaddleOCR + MinerU HTTP 客户端占位
