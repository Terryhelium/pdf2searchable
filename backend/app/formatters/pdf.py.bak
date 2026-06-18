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

        for pi, pdata in enumerate(pages):
            if pi >= len(doc):
                break
            page = doc[pi]
            pw, ph = page.rect.width, page.rect.height
            pruned = pdata.get("prunedResult", {})
            blocks = pruned.get("parsing_res_list", [])
            ow, oh = pruned.get("width", 1), pruned.get("height", 1)
            sx, sy = pw / ow, ph / oh

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
                text = blk["block_content"]
                try:
                    rect = fitz.Rect(bb[0]*sx, bb[1]*sy, bb[2]*sx, bb[3]*sy)
                    for fs in [10, 8, 6, 5, 4]:
                        rc = page.insert_textbox(rect, text, fontname=fname,
                            fontsize=fs, render_mode=3, overlay=True)
                        if rc >= 0 or rc < -100:
                            break
                        page.clean_contents()
                except Exception:
                    pass

        doc.save(str(output_path), garbage=4, deflate=True)
        doc.close()

        verify = fitz.open(str(output_path))
        chars = sum(len(verify[i].get_text().strip()) for i in range(len(verify)))
        logger.info("PDF: %s (%d页 %d字符)", output_path, len(verify), chars)
        verify.close()
        return [output_path]
