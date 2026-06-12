from __future__ import annotations

import logging
from pathlib import Path

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class TextFormatter(BaseFormatter):
    name = "txt"

    def __init__(self, ocr_data: dict):
        self.ocr_data = ocr_data

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """提取纯文本（按 MinerU 阅读顺序）"""
        stem = input_path.stem
        output_path = output_dir / f"{stem}.txt"

        # TODO: 对接OCR服务器后实现
        # 1. 优先用 MinerU 的结构化输出（按阅读顺序排列）
        # 2. 表格保留 tab 分隔格式
        # 3. 段落间空行分隔
        output_path.write_text(f"[placeholder] OCR text for {input_path.name}")

        logger.info("Generated TXT: %s", output_path)
        return [output_path]
