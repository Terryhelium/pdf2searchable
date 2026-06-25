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
- [x] 旋转页面处理
- [x] 文档：交付文档 / 服务调度速查 / 离线打包指南

---

## 2026-06-25 可搜索PDF坐标对齐 — 重大进展

### 已解决：旋转扫描件搜索高亮偏移

**最终方案**：OCRmyPDF + PaddleOCR 插件

- OCRmyPDF 负责坐标对齐（渲染同一张图做 OCR 和底图）
- PaddleOCR 负责中文识别质量
- 旋转页面自动处理，输出 rotation=0

**验证结果**（CPU 版，153 容器内）：

| 样本 | 旋转 | 页数 | 字符 | 效果 |
|------|------|------|------|------|
| 22000 采购合同 | 90° | 3 | 2271 | 高亮准确 ✓ |
| 验收文档 | 270° | 1 | 1068 | 高亮准确 ✓ |

### 当前部署状态

**148 服务器**（生产）：
- `pdf2searchable-backend` 容器内已安装 `ocrmypdf` + `ocrmypdf-paddleocr`（CPU 版）
- `pdf.py` 调用 OCRmyPDF 命令行处理 PDF 格式
- 可用，但速度慢（3 页约 2-3 分钟）

**153 服务器**（算力）：
- `ocrmypdf-gpu` 容器已构建（`ocrmypdf-gpu:latest`）
- 包含：Python 3.11 + OCRmyPDF 17.7.0 + PaddleOCR 3.7.0 + PaddlePaddle 2.6.1 GPU
- HTTP 服务 `server.py` 在 8090 端口
- **问题**：PaddlePaddle 2.6.1 和 PaddleOCR 3.x 不兼容，当前只能用 CPU

### GPU 加速 — 待解决

**根因**：基础镜像 `paddle:2.6.1-gpu-cuda11.7` 的 PaddlePaddle 版本太旧

**解决方案**（已确认可行）：
```bash
# 在 153 ocrmypdf-gpu 容器内执行
pip install paddlepaddle-gpu==3.2.2 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
```

- CUDA 12.6 的 paddlepaddle-gpu 3.2.2 可用
- 153 的 CUDA 12.2 向下兼容 CUDA 12.6
- 装完后重启容器即可

**预期效果**：GPU 加速后 3 页 PDF 预计 10-20 秒（当前 CPU 约 2-3 分钟）

### 148 后端改造 — 待完成

148 后端需要改为调用 153 的 OCRmyPDF GPU 服务（8090 端口），而不是本地 CPU 处理。

修改 `backend/app/formatters/pdf.py`：
- 把 `ocrmypdf` 命令行调用改为 HTTP POST 到 `http://10.19.26.153:8090/ocr`
- 传入 PDF 文件，接收处理后的可搜索 PDF

### 专家建议记录

1. OCRmyPDF 坐标对齐正确的关键：**OCR 用的图和 PDF 底图是同一张图**
2. 原版插件使用 word-level 坐标（`rec_boxes` + `text_word_region`），远程 API 只返回 block-level 坐标（`block_bbox`），格式不匹配
3. PaddleOCR-VL（153 现有服务）和标准 PaddleOCR 是不同的东西，VL 版不返回 word-level 坐标
4. `ocrmypdf-paddleocr` 插件要求 `paddlepaddle>=3.0.0`，2.6.x 不兼容

---

## 后续规划

### 立即执行（明天）
- [ ] 153 容器内装 `paddlepaddle-gpu==3.2.2`（cu126 源）
- [ ] 重启 ocrmypdf-gpu 容器，验证 GPU 生效
- [ ] 测试 GPU 处理速度
- [ ] 修改 148 `pdf.py` 调用 153 的 8090 服务
- [ ] 端到端测试：网页上传 → GPU 处理 → 下载可搜索 PDF

### v2.1 — 体验增强
- [ ] 文件预览（PDF/图片在线查看）
- [ ] 处理进度百分比 / 预计时间
- [ ] 输出文件打包 ZIP 下载

### v2.2 — 生产加固
- [ ] Docker 镜像瘦身
- [ ] 操作手册 USER_MANUAL.md
- [ ] Docker 卷定期备份策略
- [ ] 前端主题切换修复
- [ ] 产品名改为 `档案数字化平台`
