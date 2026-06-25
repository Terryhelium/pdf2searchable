"""OCRmyPDF GPU HTTP Service

POST /ocr  — 上传 PDF，返回可搜索 PDF
GET  /health — 健康检查
"""

import logging
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="OCRmyPDF GPU Service")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ocr")
async def ocr_pdf(
    file: UploadFile = File(...),
    lang: str = "chi_sim+chi_tra",
):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.pdf"
        output_path = Path(tmpdir) / "output.pdf"

        content = await file.read()
        input_path.write_bytes(content)

        cmd = [
            "ocrmypdf",
            "--plugin", "ocrmypdf_paddleocr",
            "-l", lang,
            "--rotate-pages",
            "--deskew",
            "--force-ocr",
            "--output-type", "pdf",
            str(input_path),
            str(output_path),
        ]
        log.info("OCRmyPDF: processing %s (%d bytes)", file.filename, len(content))

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if proc.returncode not in (0, 6):
            log.error("OCRmyPDF failed (rc=%d): %s", proc.returncode, proc.stderr[-500:])
            return Response(
                content=f"OCRmyPDF failed: {proc.stderr[-200:]}",
                status_code=500,
            )

        if not output_path.exists():
            return Response(content="Output file not created", status_code=500)

        output_bytes = output_path.read_bytes()
        log.info("OCRmyPDF: done, %d bytes output", len(output_bytes))

        return Response(
            content=output_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
        )
