# SPDX-License-Identifier: MPL-2.0
"""OCRmyPDF plugin: remote PaddleOCR-VL engine via HTTP API."""

from __future__ import annotations

import logging

from ocrmypdf import hookimpl

log = logging.getLogger(__name__)


@hookimpl
def initialize(plugin_manager):
    pass


@hookimpl
def check_options(options):
    pass


@hookimpl
def get_ocr_engine():
    from ocrmypdf_paddleocr_remote.engine import PaddleOcrEngine
    return PaddleOcrEngine()
