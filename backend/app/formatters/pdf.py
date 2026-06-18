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

        # 用 OCR 渲染尺寸重建PDF：OCR 坐标 = 图片坐标 = 页面坐标，1:1
        src = fitz.open(str(input_path))
        doc_out = fitz.Document()
        font = fitz.Font("cjk")
        fname = font.name.replace(" ", "")

        for pi, pdata in enumerate(pages):
            if pi >= len(src):
                break

            # 渲染底图（与发给 PaddleOCR 的方式一致）
            page = src[pi]
            pix = page.get_pixmap(matrix=fitz.Matrix(144.0/72.0, 144.0/72.0))
            pw, ph = pix.width, pix.height

            # OCR 数据中的宽高
            pruned = pdata.get("prunedResult", {})
            blocks = pruned.get("parsing_res_list", [])
            ow = pruned.get("width") or pw
            oh = pruned.get("height") or ph
            sx, sy = pw / ow, ph / oh

            # 过滤文字块
            tb = [b for b in blocks
                  if b.get("block_content","") and b.get("block_bbox")
                  and len(b["block_bbox"]) >= 4
                  and b.get("block_label","") not in ("figure","image","seal")]

            # 新建页 + 插入底图
            new_page = doc_out.new_page(-1, width=pw, height=ph)
            new_page.insert_image(new_page.rect, stream=pix.tobytes("jpeg"))

            if not tb:
                continue

            # 注册 CJK 字体
            tmp = tempfile.NamedTemporaryFile(suffix=".otf", delete=False)
            try:
                tmp.write(font.buffer)
                tmp.close()
                new_page.insert_font(fontfile=tmp.name, fontname=fname)
            except Exception:
                pass
            finally:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass

            # 叠文字（坐标 1:1）
            for blk in tb:
                bb = blk["block_bbox"]
                text = blk["block_content"]
                try:
                    rect = fitz.Rect(bb[0]*sx, bb[1]*sy, bb[2]*sx, bb[3]*sy)
                    for fs in [10, 8, 6, 5, 4]:
                        rc = new_page.insert_textbox(
                            rect, text, fontname=fname, fontsize=fs,
                            render_mode=3, overlay=True,
                        )
                        if rc >= 0 or rc < -100:
                            break
                        new_page.clean_contents()
                except Exception:
                    pass

        src.close()
        doc_out.save(str(output_path), garbage=4, deflate=True)
        doc_out.close()

        verify = fitz.open(str(output_path))
        chars = sum(len(verify[i].get_text().strip()) for i in range(len(verify)))
        logger.info("PDF: %s (%d页 %d字符)", output_path, len(verify), chars)
        verify.close()
        return [output_path]
