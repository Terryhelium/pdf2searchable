# SPDX-License-Identifier: MPL-2.0
"""PaddleOCR engine that calls remote GPU API instead of local Python API."""

from __future__ import annotations

import base64
import logging
import math
import os
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from PIL import Image

from ocrmypdf.models.ocr_element import BoundingBox, OcrClass, OcrElement
from ocrmypdf.pluginspec import OcrEngine, OrientationConfidence

from ocrmypdf_paddleocr.lang_map import SUPPORTED_LANGUAGES

if TYPE_CHECKING:
    from ocrmypdf._options import OcrOptions

log = logging.getLogger(__name__)

PADDLEOCR_API_URL = os.environ.get("PADDLEOCR_API_URL", "http://10.19.26.153:8080")
PADDLEOCR_TIMEOUT = int(os.environ.get("PADDLEOCR_TIMEOUT", "120"))


def _call_remote_ocr(image_path: str) -> dict | None:
    """Call remote PaddleOCR API and return parsed results."""
    url = f"{PADDLEOCR_API_URL}/layout-parsing"

    with open(image_path, "rb") as f:
        img_data = f.read()

    b64 = base64.b64encode(img_data).decode()
    payload = {"file": b64, "fileType": 1, "useLayoutDetection": True}

    try:
        with httpx.Client(timeout=PADDLEOCR_TIMEOUT) as client:
            resp = client.post(url, json=payload)
            if resp.is_error:
                log.error("Remote PaddleOCR error: %s", resp.status_code)
                return None
            result = resp.json()
            if result.get("errorCode", 0) != 0:
                log.error("Remote PaddleOCR: %s", result.get("errorMsg", ""))
                return None
            return result
    except Exception as e:
        log.error("Remote PaddleOCR failed: %s", e)
        return None


def _quad_to_bbox(quad) -> BoundingBox | None:
    """Convert a 4-point quad to BoundingBox."""
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    left, right = float(min(xs)), float(max(xs))
    top, bottom = float(min(ys)), float(max(ys))
    if right <= left or bottom <= top:
        return None
    return BoundingBox(left=left, top=top, right=right, bottom=bottom)


class PaddleOcrEngine(OcrEngine):
    """OCR engine using remote PaddleOCR-VL API."""

    @staticmethod
    def version() -> str:
        return "remote-vl"

    @staticmethod
    def creator_tag(options: OcrOptions) -> str:
        return "PaddleOCR-VL Remote"

    def __str__(self) -> str:
        return "PaddleOCR-VL Remote"

    @staticmethod
    def languages(options: OcrOptions) -> set[str]:
        return SUPPORTED_LANGUAGES

    @staticmethod
    def get_orientation(
        input_file: Path, options: OcrOptions
    ) -> OrientationConfidence:
        return OrientationConfidence(angle=0, confidence=0.0)

    @staticmethod
    def get_deskew(input_file: Path, options: OcrOptions) -> float:
        return 0.0

    @staticmethod
    def supports_generate_ocr() -> bool:
        return True

    @staticmethod
    def generate_ocr(
        input_file: Path,
        options: OcrOptions,
        page_number: int = 0,
    ) -> tuple[OcrElement, str]:
        with Image.open(input_file) as img:
            img_width, img_height = img.size
            dpi_info = img.info.get('dpi', (300, 300))
            dpi = float(dpi_info[0] if isinstance(dpi_info, tuple) else dpi_info)

        page = OcrElement(
            ocr_class=OcrClass.PAGE,
            bbox=BoundingBox(left=0, top=0, right=img_width, bottom=img_height),
            dpi=dpi,
            page_number=page_number,
        )

        result = _call_remote_ocr(str(input_file))
        if not result:
            return page, ""

        layout_results = result.get("result", {}).get("layoutParsingResults", [])
        if not layout_results:
            return page, ""

        text_parts = []

        for lr in layout_results:
            pruned = lr.get("prunedResult", {})
            blocks = pruned.get("parsing_res_list", [])

            for blk in blocks:
                content = (blk.get("block_content") or "").strip()
                bbox = blk.get("block_bbox")
                label = blk.get("block_label", "")

                if not content or not bbox or len(bbox) < 4:
                    continue
                if label in ("figure", "image", "seal"):
                    continue

                x1, y1, x2, y2 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                if x2 <= x1 or y2 <= y1:
                    continue

                line_bbox = BoundingBox(left=x1, top=y1, right=x2, bottom=y2)
                line = OcrElement(ocr_class=OcrClass.LINE, bbox=line_bbox)

                word = OcrElement(
                    ocr_class=OcrClass.WORD,
                    bbox=line_bbox,
                    text=content,
                    confidence=0.9,
                )
                line.children.append(word)
                page.children.append(line)
                text_parts.append(content)

        full_text = '\n'.join(text_parts)
        return page, full_text

    @staticmethod
    def generate_hocr(input_file, output_hocr, output_text, options):
        raise NotImplementedError("Use generate_ocr()")

    @staticmethod
    def generate_pdf(input_file, output_pdf, output_text, options):
        raise NotImplementedError("Use generate_ocr()")
