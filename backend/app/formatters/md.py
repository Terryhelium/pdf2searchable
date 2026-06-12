from __future__ import annotations

import logging
from pathlib import Path

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class MarkdownFormatter(BaseFormatter):
    name = "md"

    def __init__(self, ocr_data: dict):
        self.ocr_data = ocr_data

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """生成结构化Markdown（利用 MinerU 的文档结构理解）"""
        stem = input_path.stem
        output_path = output_dir / f"{stem}.md"

        # TODO: 对接OCR服务器后实现
        # MinerU 是关键：它输出标题层级、表格结构、阅读顺序
        # 1. 标题 → # heading 级别
        # 2. 表格 → Markdown 表格语法（| 列1 | 列2 |）
        # 3. 段落 → 普通文本
        # 4. 图片 → ![title](path) 引用
        output_path.write_text(f"[placeholder] Markdown for {input_path.name}")

        logger.info("Generated MD: %s", output_path)
        return [output_path]
