from __future__ import annotations

import logging
import re
from pathlib import Path

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class MarkdownFormatter(BaseFormatter):
    name = "md"

    def __init__(self, ocr_data: dict):
        self.ocr_data = ocr_data

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """生成结构化 Markdown（利用 MinerU 的 md_content）"""
        stem = input_path.stem
        output_path = output_dir / f"{stem}.md"

        mineru_data = ocr_data.get("mineru", {})
        md_content = (mineru_data.get("md_content") or "").strip()
        if md_content:
            md_content = self._clean_mineru_md(md_content)

        if not md_content:
            # 回退：从 content_list 手动构建 markdown
            md_content = self._build_from_content_list(mineru_data)
        if not md_content:
            # 再回退：从 PaddleOCR 文字块构建简单文本
            md_content = self._fallback_from_paddle(ocr_data.get("paddleocr", {}))

        output_path.write_text(md_content, encoding="utf-8")
        logger.info("生成 MD: %s (%d 字符)", output_path, len(md_content))
        return [output_path]

    @staticmethod
    def _clean_mineru_md(md: str) -> str:
        """清理 MinerU 生成的 MD 中的 LaTeX 公式标记等乱码"""
        # 图片引用转文字描述（因为图片不返回，避免破损图标）
        md = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'[图片: \1]', md)
        md = re.sub(r'!\[\]\([^)]*\)', '[图片]', md)
        # 去掉行内公式 $...$，保留中间文字
        md = re.sub(r'\$\s*\^?\{\{?\*\}?\}\s*\$', '*', md)
        md = re.sub(r'\$\$\s*(.*?)\s*\$\$', r'\1', md, flags=re.DOTALL)
        md = re.sub(r'\$(.*?)\$', r'\1', md)
        # 去掉 ^{}  _{} 等 LaTeX 命令
        md = re.sub(r'\^\{[^}]*\}', '', md)
        md = re.sub(r'\_\{[^}]*\}', '', md)
        # 清理多余的花括号
        md = md.replace('{{', '{').replace('}}', '}')
        return md

    def _build_from_content_list(self, mineru_data: dict) -> str:
        """从 MinerU content_list 构建 Markdown"""
        content_list = mineru_data.get("content_list")
        if not isinstance(content_list, list):
            return ""

        lines: list[str] = []
        for item in content_list:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type", "")
            text = (item.get("text") or "").strip()
            if not text:
                continue

            if item_type == "heading":
                level = item.get("level", 1)
                lines.append(f"{'#' * level} {text}")
            elif item_type == "list":
                lines.append(f"- {text}")
            elif item_type == "table":
                lines.append(text)
            elif item_type == "figure":
                caption = item.get("caption", "")
                if caption:
                    lines.append(f"![{caption}]({item.get('image_path', '')})")
            else:
                lines.append(text)
            lines.append("")

        return "\n".join(lines).strip()

    def _fallback_from_paddle(self, paddle_data: dict) -> str:
        """回退：从 PaddleOCR 文字块构建简单 markdown"""
        pages = (
            paddle_data.get("result", {})
            .get("layoutParsingResults", [])
        )
        lines: list[str] = []
        for page in pages:
            pruned = page.get("prunedResult", {})
            blocks = pruned.get("parsing_res_list", [])
            sorted_blocks = sorted(
                blocks,
                key=lambda b: (b.get("block_bbox", [0, 0])[1], b.get("block_bbox", [0, 0])[0]),
            )
            for blk in sorted_blocks:
                text = (blk.get("block_content") or "").strip()
                label = blk.get("block_label", "")
                if text and label not in ("figure", "image", "seal"):
                    if label == "heading":
                        lines.append(f"# {text}")
                    else:
                        lines.append(text)
            lines.append("---")
        return "\n\n".join(lines).strip()
