from __future__ import annotations

import logging
from pathlib import Path

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class SearchablePDFFormatter(BaseFormatter):
    name = "pdf"

    def __init__(self, ocr_data: dict):
        self.ocr_data = ocr_data

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """生成可搜索PDF：原图 + 覆盖OCR文字层"""
        stem = input_path.stem
        output_path = output_dir / f"{stem}_searchable.pdf"

        # TODO: 对接OCR服务器后实现
        # 1. 用 Pillow 把原图转成 PDF 底图
        # 2. 用 pypdf 叠加文字层（使用 PaddleOCR 精确坐标）
        # 3. 文字层不可见但可选（透明文字覆盖）
        output_path.write_text(f"[placeholder] searchable PDF for {input_path.name}")

        logger.info("Generated PDF: %s", output_path)
        return [output_path]
