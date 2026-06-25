from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path

import fitz

from app.formatters import BaseFormatter, registry

logger = logging.getLogger(__name__)

OCRMYPDF_LANG = "chi_sim+chi_tra"


@registry.register
class SearchablePDFFormatter(BaseFormatter):
    name = "pdf"

    def __init__(self, ocr_data: dict):
        pass

    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        stem = input_path.stem
        output_path = output_dir / f"{stem}_searchable.pdf"

        if shutil.which("ocrmypdf"):
            return await self._format_with_ocrmypdf(input_path, output_path)

        logger.warning("ocrmypdf not found, falling back to original PDF copy")
        src = fitz.open(str(input_path))
        src.save(str(output_path), garbage=4)
        src.close()
        return [output_path]

    @staticmethod
    async def _format_with_ocrmypdf(input_path: Path, output_path: Path) -> list[Path]:
        cmd = [
            "ocrmypdf",
            "--plugin", "ocrmypdf_paddleocr",
            "-l", OCRMYPDF_LANG,
            "--force-ocr",
            "--output-type", "pdf",
            str(input_path),
            str(output_path),
        ]
        logger.info("OCRmyPDF: %s", " ".join(cmd))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode not in (0, 6):
            logger.error("OCRmyPDF failed (rc=%d): %s", proc.returncode, stderr.decode()[-500:])
            raise RuntimeError(f"OCRmyPDF failed with exit code {proc.returncode}")

        if stdout:
            logger.info("OCRmyPDF: %s", stdout.decode()[-300:])

        verify = fitz.open(str(output_path))
        chars = sum(len(verify[i].get_text().strip()) for i in range(len(verify)))
        logger.info("PDF: %s (%d页 %d字符)", output_path, len(verify), chars)
        verify.close()
        return [output_path]
