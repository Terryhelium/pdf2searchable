from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class JPEGFormatter(BaseFormatter):
    name = "jpeg"

    MAX_WIDTH = 1200

    def __init__(self, ocr_data: dict):
        self.ocr_data = ocr_data

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """生成预览用 JPEG（每页一张）"""
        stem = input_path.stem
        ext = input_path.suffix.lower()

        if ext == ".pdf":
            images = self._pdf_to_images(input_path)
        else:
            img = Image.open(str(input_path))
            images = [img]

        paths: list[Path] = []
        for page_idx, img in enumerate(images):
            page_num = page_idx + 1
            output_path = output_dir / f"{stem}_p{page_num}.jpg"

            # 缩放至合适预览尺寸
            if img.width > self.MAX_WIDTH:
                ratio = self.MAX_WIDTH / img.width
                new_h = int(img.height * ratio)
                img = img.resize((self.MAX_WIDTH, new_h), Image.LANCZOS)

            # 转换 RGB 并保存
            if img.mode == "RGBA":
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

            img.save(str(output_path), format="JPEG", quality=85)
            paths.append(output_path)
            if page_idx > 0:
                img.close()

        if images:
            images[0].close()

        logger.info("生成 JPEG: %s (%d 页)", output_dir / f"{stem}_p*.jpg", len(paths))
        return paths

    @staticmethod
    def _pdf_to_images(input_path: Path, dpi: int = 150) -> list[Image.Image]:
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
