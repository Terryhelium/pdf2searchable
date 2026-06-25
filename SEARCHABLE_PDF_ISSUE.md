# 可搜索 PDF 坐标对齐问题 — 技术分析

## 目标

将扫描版 PDF 转换为可搜索 PDF：在扫描图上叠加隐藏文字层，使 Ctrl+F 搜索时高亮位置准确贴合原文。

## 当前架构

- **148 服务器**：FastAPI 后端 + React 前端（Docker Compose）
- **153 服务器**：PaddleOCR-VL (GPU, :8080) + MinerU (:8000)

## 已验证可行的方案

### OCRmyPDF + 本地 PaddleOCR 插件（CPU）

```bash
ocrmypdf --plugin ocrmypdf_paddleocr -l chi_sim --rotate-pages --deskew --force-ocr input.pdf output.pdf
```

**效果**：搜索高亮基本准确，文字识别质量好。

**问题**：
- PaddleOCR 跑在 148 容器内 CPU 上，3 页 PDF 处理约 1-2 分钟
- 153 GPU 服务器闲置

### OCRmyPDF + Tesseract（CPU）

```bash
ocrmypdf -l chi_sim+chi_tra --rotate-pages --deskew --force-ocr input.pdf output.pdf
```

**效果**：搜索高亮准确，但中文识别质量差（字符断裂、错字）。

## 已尝试但失败的方案

### 1. 自研方案：PaddleOCR API + PyMuPDF 叠字

流程：
1. 调用 153 PaddleOCR API 获取 OCR 坐标
2. 用 PyMuPDF 在原 PDF 上 `insert_textbox()` 叠加隐藏文字

**失败原因**：`insert_textbox()` 在旋转页面上使用内部坐标系（mediabox），与 PaddleOCR 返回的 display 坐标系不一致。文字写入位置错误。

### 2. 自研方案：提取扫描图 + 旋转 + 重建页面

流程：
1. 提取原始扫描图（3507x2480）
2. 用 Pillow 旋转 90°
3. 创建 rotation=0 新页面，嵌入旋转后的图
4. 在新页面上叠字

**失败原因**：文件体积膨胀 4-5 倍，搜索高亮仍有偏移。

### 3. 自研方案：PyMuPDF 渲染 + 发图给 PaddleOCR + 同图做底图

流程：
1. PyMuPDF `get_pixmap()` 渲染页面为 300 DPI PNG
2. 发 PNG 给 153 PaddleOCR API
3. 用同一张 PNG 做 PDF 底图
4. OCR 坐标直接写入

**失败原因**：文件体积膨胀，高亮偏移（PaddleOCR API 返回的坐标与渲染图坐标有偏差）。

### 4. OCRmyPDF + 远程 PaddleOCR API 插件（自研适配器）

流程：
1. 写适配器插件，模拟 `PaddleOCR.predict()` 接口
2. 内部发 HTTP 请求到 153 PaddleOCR-VL API (:8080/layout-parsing)
3. OCRmyPDF 处理坐标对齐

**失败原因**：
- 153 API 返回的是 block-level 坐标（较大区域）
- 原版插件使用 word-level 坐标（精确到词）
- OCRmyPDF 内部对坐标格式有特定要求
- 输出效果与原版插件差距很大

## 核心问题

OCRmyPDF 坐标对齐正确的关键是：
1. 用同一个渲染图做 OCR 和做底图
2. OCR 引擎返回的坐标格式与 OCRmyPDF 内部处理逻辑匹配

原版 `ocrmypdf-paddleocr` 插件使用 `paddleocr.PaddleOCR.predict()` 返回的 `rec_boxes`（行级坐标）和 `text_word_region`（词级坐标），这些格式与 OCRmyPDF 的 `OcrElement` 模型完美匹配。

153 的 PaddleOCR-VL HTTP API 返回的是 `block_bbox`（块级坐标），格式和精度都不匹配。

## 专家待解答问题

1. **能否让 OCRmyPDF 的 PaddleOCR 插件使用 GPU？**
   - 当前插件 `_create_paddle_engine()` 没有传 `device='gpu'` 参数
   - 148 容器内没有 GPU，也没有安装 PaddlePaddle GPU 版
   - 如果在 148 安装 PaddlePaddle GPU 版，需要 NVIDIA Container Toolkit 支持

2. **能否改造 153 PaddleOCR API 返回 word-level 坐标？**
   - 当前 `/layout-parsing` API 返回 block-level `block_bbox`
   - 是否有参数可以返回更细粒度的坐标？
   - PaddleOCR-VL 是否支持类似 `return_word_box=True` 的 HTTP API 参数？

3. **有没有其他 GPU 加速的可搜索 PDF 方案？**
   - 汉王 OCR 等商业方案是如何做到 GPU 加速 + 坐标对齐的？
   - 是否有开源方案可以参考？

4. **能否在 153 上直接运行 OCRmyPDF？**
   - 153 宿主机没有 PaddlePaddle，只有 Docker 容器内有
   - 能否在 153 的 PaddleOCR 容器内安装 OCRmyPDF？
   - 或者创建一个新的 Docker 容器，包含 OCRmyPDF + PaddlePaddle GPU？

## 相关文件

- `backend/app/formatters/pdf.py` — 当前使用 OCRmyPDF + 原版插件（CPU）
- `backend/app/ocr.py` — PDF 格式不调用 PaddleOCR API（由 OCRmyPDF 内部处理）
- `backend/ocrmypdf_paddleocr_remote/` — 远程 API 适配器（效果差，未使用）
- `cases/` — 测试用旋转扫描 PDF 样本

## 测试样本

| 文件 | 旋转 | 页数 | 说明 |
|------|------|------|------|
| 14-2026_档案馆_终端安全管理_22000.pdf | 90° | 3 | 采购合同，纯扫描 |
| 宁波市档案馆终端安全管理系统验收文档.pdf | 270° | 1 | 验收文档，纯扫描 |
