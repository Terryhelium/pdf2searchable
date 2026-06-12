from __future__ import annotations

import logging
from pathlib import Path

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class TIFFFormatter(BaseFormatter):
    name = "tiff"

    def __init__(self, ocr_data: dict):
        self.ocr_data = ocr_data

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """生成归档级TIFF（LZW压缩）"""
        stem = input_path.stem
        output_path = output_dir / f"{stem}.tiff"

        # TODO: 对接OCR服务器后实现
        # 1. 如果输入是 PDF，用 Pillow/PyMuPDF 逐页转图像
        # 2. 多页合成一个 TIFF + LZW 压缩
        # 3. 单页直接转 TIFF
        output_path.write_text(f"[placeholder] archive TIFF for {input_path.name}")

        logger.info("Generated TIFF: %s", output_path)
        return [output_path]
