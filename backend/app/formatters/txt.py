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
        """提取纯文本（优先用 MinerU 阅读顺序，回退到 PaddleOCR 文字块）"""
        stem = input_path.stem
        output_path = output_dir / f"{stem}.txt"

        text = self._extract_mineru_text(ocr_data.get("mineru", {}))
        if not text:
            text = self._extract_paddle_text(ocr_data.get("paddleocr", {}))

        output_path.write_text(text, encoding="utf-8")
        logger.info("生成 TXT: %s (%d 字符)", output_path, len(text))
        return [output_path]

    def _extract_mineru_text(self, mineru_data: dict) -> str:
        """从 MinerU content_list 按阅读顺序提取文本"""
        content_list = mineru_data.get("content_list")
        if isinstance(content_list, list) and content_list:
            parts: list[str] = []
            for item in content_list:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type", "")
                text = item.get("text", "") or ""
                if not text.strip():
                    continue
                if item_type in ("table",):
                    parts.append(text)
                elif item_type in ("text", "heading", "list"):
                    parts.append(text)
                # figure/caption 等跳过或取描述文本
                elif item_type == "figure":
                    caption = item.get("caption", "")
                    if caption:
                        parts.append(f"[图片: {caption}]")
            if parts:
                return "\n\n".join(parts) + "\n"

        # 回退：从 md_content 提取纯文本
        md = mineru_data.get("md_content", "") or ""
        if md:
            return self._strip_markdown(md) + "\n"
        return ""

    def _extract_paddle_text(self, paddle_data: dict) -> str:
        """从 PaddleOCR-VL 文字块提取纯文本（按坐标排序）"""
        pages = (
            paddle_data.get("result", {})
            .get("layoutParsingResults", [])
        )
        parts: list[str] = []
        for page in pages:
            pruned = page.get("prunedResult", {})
            blocks = pruned.get("parsing_res_list", [])
            # 按行排序（先按 Y 再按 X 阅读顺序）
            sorted_blocks = sorted(
                blocks,
                key=lambda b: (b.get("block_bbox", [0, 0])[1], b.get("block_bbox", [0, 0])[0]),
            )
            for blk in sorted_blocks:
                text = (blk.get("block_content") or "").strip()
                label = blk.get("block_label", "")
                if text and label not in ("figure", "image", "seal"):
                    parts.append(text)
            parts.append("")  # 页间空行
        return "\n".join(parts)

    @staticmethod
    def _strip_markdown(md: str) -> str:
        """简单去除 Markdown 标记，保留纯文本"""
        lines = md.splitlines()
        out: list[str] = []
        for line in lines:
            # 移除标题标记
            line = line.lstrip("#").lstrip()
            # 移除粗体/斜体
            line = line.replace("**", "").replace("*", "")
            # 移除链接标记 [text](url) → text
            import re
            line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
            # 移除图片标记
            line = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", line)
            # 移除表格分隔行
            if re.match(r"^[\s\|:\-]+$", line):
                continue
            out.append(line.rstrip())
        return "\n".join(out)
