from __future__ import annotations

import logging
import os
from pathlib import Path

from PIL import Image

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class TIFFFormatter(BaseFormatter):
    name = "tiff"

    def __init__(self, ocr_data: dict):
        self.ocr_data = ocr_data

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """生成归档级 TIFF（LZW 压缩）"""
        stem = input_path.stem
        output_path = output_dir / f"{stem}.tiff"
        ext = input_path.suffix.lower()

        if ext == ".pdf":
            pages = self._pdf_to_images(input_path)
            if pages:
                pages[0].save(
                    str(output_path),
                    save_all=True,
                    append_images=pages[1:],
                    format="TIFF",
                    compression="tiff_lzw",
                )
                for img in pages:
                    img.close()
            else:
                output_path.write_bytes(b"")
        else:
            img = Image.open(str(input_path))
            # 转换到 RGB 模式（LZW 需要）
            if img.mode not in ("RGB", "L", "RGBA"):
                img = img.convert("RGB")
            img.save(str(output_path), format="TIFF", compression="tiff_lzw")
            img.close()

        logger.info("生成 TIFF: %s", output_path)
        return [output_path]

    @staticmethod
    def _pdf_to_images(input_path: Path, dpi: int = 200) -> list[Image.Image]:
        """用 PyMuPDF 将 PDF 每页渲染为 PIL Image"""
        import fitz

        doc = fitz.open(str(input_path))
        pages: list[Image.Image] = []
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                zoom = dpi / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                pages.append(img)
        finally:
            doc.close()
        return pages
