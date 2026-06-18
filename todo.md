# 宁波市档案馆文档OCR处理系统 开发日志

## v2.0 — 已发布（2026-06-18）

### 功能完成
- [x] 前后端分离架构，FastAPI + React + Ant Design 6
- [x] 所有 API 路由 + SQLite 数据库
- [x] PaddleOCR-VL + MinerU 双引擎集成
- [x] 6 种格式输出（PDF / TIFF / JPEG / TXT / MD / JSON）
- [x] 单文件上传 + 批量处理（服务器目录 / 本地上传）
- [x] 任务记录管理（下载 / 单删 / 批量删）
- [x] Docker Compose 部署（端口 9010）
- [x] CJK 字体嵌入（可搜索PDF中文可搜）
- [x] 自适应字号 + 每页字体注册
- [x] 文档：交付文档 / 服务调度速查 / 离线打包指南

### 已知问题
- [ ] **可搜索PDF文字偏移** — PaddleOCR 坐标与 PyMuPDF 渲染底图存在偏移，旋转页面更明显。
      记录见 `已知问题.md`，下次集中解决。

---

## 后续规划

### 近期（v2.1）
- [ ] 文件预览（PDF/图片在线查看）
- [ ] 处理进度百分比
- [ ] 输出文件打包 ZIP 下载

### 中期（v2.2）
- [ ] Docker 镜像瘦身
- [ ] 操作手册 USER_MANUAL.md
- [ ] Docker 卷定期备份策略

### PDF 偏移问题（待解决）
- [ ] 根本原因：PaddleOCR-VL 内部渲染 PDF 的方式与 PyMuPDF 不一致
- [ ] 尝试方向1：PyMuPDF 渲染 PNG → 发给 PaddleOCR → 用同样 PNG 做底图（当前尝试，仍有偏差）
- [ ] 尝试方向2：用 PaddleOCR 返回的 JSON 中的原文位置信息（block_bbox）直接映射
- [ ] 尝试方向3：不用 PaddleOCR-VL，改用 MinerU 的 content_list 坐标
- [ ] 尝试方向4：用 OCRmyPDF 或其它专门做双层 PDF 的工具替代自研方案
