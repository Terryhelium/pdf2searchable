from __future__ import annotations

import logging
from pathlib import Path

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class JPEGFormatter(BaseFormatter):
    name = "jpeg"

    def __init__(self, ocr_data: dict):
        self.ocr_data = ocr_data

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """生成预览用JPEG（每页一张）"""
        stem = input_path.stem

        # TODO: 对接OCR服务器后实现
        # 1. 如果输入是 PDF，逐页转 JPEG
        # 2. 命名规则：文件名_p{页码}.jpg
        # 3. 缩放至合适尺寸（如 1200px 宽）
        # 4. 保存为 JPEG 85% 质量
        output_path = output_dir / f"{stem}_p1.jpg"
        output_path.write_text(f"[placeholder] preview JPEG page 1 for {input_path.name}")

        logger.info("Generated JPEG: %s", output_path)
        return [output_path]
