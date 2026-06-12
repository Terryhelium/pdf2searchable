from __future__ import annotations

import json
import logging
from pathlib import Path

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class JSONFormatter(BaseFormatter):
    name = "json"

    def __init__(self, ocr_data: dict):
        self.ocr_data = ocr_data

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """生成完整OCR数据的JSON（保留版式信息，供后续NER标注）"""
        stem = input_path.stem
        output_path = output_dir / f"{stem}.json"

        # JSON 可以提前实现大部分逻辑，不需要OCR服务器
        output = {
            "source": input_path.name,
            "ocr_engine": {
                "paddleocr": ocr_data.get("paddleocr"),
                "mineru": ocr_data.get("mineru"),
            },
            "content": ocr_data,
            "meta": {
                "generated_at": __import__("datetime").datetime.now().isoformat(),
                "format_version": "1.0",
            },
        }

        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
        logger.info("Generated JSON: %s", output_path)
        return [output_path]
