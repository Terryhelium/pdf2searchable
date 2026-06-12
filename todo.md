# 宁波市档案馆文档OCR处理系统 开发计划

## 第一阶段：基础框架 ✅
- [x] 依赖全部升级至最新（antd 6, vite 8, TS 6, FastAPI 0.136）
- [x] 项目更名：pdf2searchable → 宁波市档案馆文档OCR处理系统
- [x] 后端路由/数据库/OCR 骨架 + 统计接口 /api/stats
- [x] 前端页面：仪表盘、单文件上传、批量处理
- [x] 侧边导航栏 + 深色/浅色模式 + 主题色切换
- [x] 输出格式选择（PDF / TIFF / JPEG / TXT / Markdown）
- [x] 异常处理修复 + 单文件处理流程修复 + 路径本地化
- [x] .gitignore + CLAUDE.md + todo.md

## 第二阶段：接入 OCR 服务器后（待网络就绪）
- [ ] 验证 PaddleOCR / MinerU 真实 API 端点
- [ ] 实现多格式输出生成（可搜索PDF / TIFF / JPEG / TXT / MD）
- [ ] 端到端单文件处理流程测试
- [ ] 端到端批量处理流程测试
- [ ] docker compose up 完整部署验证

## 第三阶段：上线准备
- [ ] NAS 挂载路径确认与配置
- [ ] 镜像体积优化
- [ ] 生产部署文档
