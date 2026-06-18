from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import fitz

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)


@registry.register
class SearchablePDFFormatter(BaseFormatter):
    name = "pdf"
    _FONT_SIZES = (10, 8, 6, 5, 4, 3, 2)

    def __init__(self, ocr_data: dict):
        pass

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        stem = input_path.stem
        output_path = output_dir / f"{stem}_searchable.pdf"

        paddle = ocr_data.get("paddleocr", {})
        pages = paddle.get("result", {}).get("layoutParsingResults", [])

        if not pages:
            src = fitz.open(str(input_path))
            src.save(str(output_path), garbage=4)
            src.close()
            return [output_path]

        doc = fitz.open(str(input_path))
        font = fitz.Font("cjk")
        fname = font.name.replace(" ", "")
        total_blocks = 0
        fitted_blocks = 0
        fallback_blocks = 0

        for pi, pdata in enumerate(pages):
            if pi >= len(doc):
                break
            page = doc[pi]
            pruned = pdata.get("prunedResult", {})
            blocks = pruned.get("parsing_res_list", [])
            ow, oh = pruned.get("width", 1), pruned.get("height", 1)
            if not ow or not oh:
                logger.warning("PDF page %d missing OCR dimensions, skip overlay", pi + 1)
                continue

            tb = [b for b in blocks if b.get("block_content","") and b.get("block_bbox") and len(b["block_bbox"])>=4 and b.get("block_label","") not in ("figure","image","seal")]
            if not tb:
                continue

            # 每页注册字体
            tmp = tempfile.NamedTemporaryFile(suffix=".otf", delete=False)
            try:
                tmp.write(font.buffer); tmp.close()
                page.insert_font(fontfile=tmp.name, fontname=fname)
            except Exception:
                pass
            finally:
                try: os.unlink(tmp.name)
                except: pass

            for blk in tb:
                bb = blk["block_bbox"]
                text = (blk["block_content"] or "").strip()
                if not text:
                    continue
                total_blocks += 1
                try:
                    rect = self._map_bbox_to_page_rect(page, bb, ow, oh)
                    if rect.is_empty or rect.width <= 1 or rect.height <= 1:
                        logger.warning("Skip tiny OCR rect on page %d: %s", pi + 1, bb)
                        continue

                    inserted = False
                    for fs in self._FONT_SIZES:
                        rc = page.insert_textbox(rect, text, fontname=fname,
                            fontsize=fs, render_mode=3, overlay=True)
                        if rc >= 0:
                            fitted_blocks += 1
                            inserted = True
                            break
                    if inserted:
                        continue

                    # Fallback: keep text searchable even if the block cannot fit inside its bbox.
                    fallback_size = max(1.5, min(3.0, rect.height * 0.35))
                    insert_at = fitz.Point(rect.x0, min(rect.y1 - 0.5, rect.y0 + fallback_size))
                    page.insert_text(
                        insert_at,
                        text,
                        fontname=fname,
                        fontsize=fallback_size,
                        render_mode=3,
                        overlay=True,
                    )
                    fallback_blocks += 1
                    logger.warning(
                        "Fallback PDF text overlay on page %d block=%s rect=%s",
                        pi + 1,
                        blk.get("block_label", ""),
                        tuple(round(v, 2) for v in rect),
                    )
                except Exception:
                    logger.exception("Failed to overlay OCR block on page %d", pi + 1)

        doc.save(str(output_path), garbage=4, deflate=True)
        doc.close()

        verify = fitz.open(str(output_path))
        chars = sum(len(verify[i].get_text().strip()) for i in range(len(verify)))
        logger.info(
            "PDF: %s (%d页 %d字符, blocks=%d, fitted=%d, fallback=%d)",
            output_path,
            len(verify),
            chars,
            total_blocks,
            fitted_blocks,
            fallback_blocks,
        )
        verify.close()
        return [output_path]

    def _map_bbox_to_page_rect(
        self,
        page: fitz.Page,
        bbox: list[float],
        ocr_width: float,
        ocr_height: float,
    ) -> fitz.Rect:
        display_w = float(page.rect.width)
        display_h = float(page.rect.height)
        base_w = float(page.mediabox.width)
        base_h = float(page.mediabox.height)

        display_score = abs((ocr_width / ocr_height) - (display_w / display_h))
        base_score = abs((ocr_width / ocr_height) - (base_w / base_h))
        use_display_coords = display_score <= base_score

        target_w = display_w if use_display_coords else base_w
        target_h = display_h if use_display_coords else base_h
        sx = target_w / ocr_width
        sy = target_h / ocr_height
        scaled = (
            float(bbox[0]) * sx,
            float(bbox[1]) * sy,
            float(bbox[2]) * sx,
            float(bbox[3]) * sy,
        )

        if not use_display_coords:
            return fitz.Rect(*scaled).normalize()

        rotation = int(page.rotation) % 360
        if rotation == 0:
            return fitz.Rect(*scaled).normalize()

        x0, y0, x1, y1 = scaled
        if rotation == 90:
            mapped = (y0, base_h - x1, y1, base_h - x0)
        elif rotation == 180:
            mapped = (base_w - x1, base_h - y1, base_w - x0, base_h - y0)
        elif rotation == 270:
            mapped = (base_w - y1, x0, base_w - y0, x1)
        else:
            mapped = scaled
        return fitz.Rect(*mapped).normalize()
