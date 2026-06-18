from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.db import Database
from app.ocr import OCRProcessor

logger = logging.getLogger(__name__)


async def process_single_file(db: Database, ocr: OCRProcessor,
                              job_id: str, file_path: Path, output_dir: Path,
                              filename: Optional[str] = None,
                              formats: Optional[list[str]] = None):
    """处理单个文件（单文件上传模式用）"""
    fname = filename or file_path.name
    try:
        await db.update_job_status(job_id, "processing")
        results = await ocr.process(str(file_path), str(output_dir), formats=formats)

        # 每个格式作为独立行写入 job_files
        file_rows = []
        for fmt, paths in results.items():
            for p in paths:
                out_name = Path(p).name
                file_rows.append((job_id, out_name, fmt, str(p)))

        if file_rows:
            await db.add_job_files_with_formats(file_rows)
        else:
            await db.add_job_files(job_id, [fname])

        await db.update_job_status(job_id, "done", processed_files=len(file_rows))
        logger.info("File processed: %s -> %s", file_path, results)
    except Exception as e:
        logger.exception("File processing failed: %s", file_path)
        err_msg = str(e)
        await db.update_job_status(job_id, "failed", processed_files=0, error_count=1)


async def run_batch_job(db: Database, ocr: OCRProcessor,
                        job_id: str, source_dir: str, dest_dir: str,
                        formats: Optional[list[str]] = None):
    """后台批量处理任务"""
    src = Path(source_dir)
    dst = Path(dest_dir)
    dst.mkdir(parents=True, exist_ok=True)

    # 扫描源目录
    files = sorted(src.iterdir()) if src.is_dir() else []
    filenames = [f.name for f in files if f.is_file()]

    if not filenames:
        await db.update_job_status(job_id, "done", total_files=0)
        return

    await db.update_job_status(job_id, "processing", total_files=len(filenames))

    processed = 0
    errors = 0

    for filename in filenames:
        file_path = src / filename
        try:
            results = await ocr.process(str(file_path), str(dst), formats=formats)
            processed += 1
        except Exception as e:
            logger.error("Batch file failed: %s - %s", filename, e)
            errors += 1
        finally:
            await db.update_job_status(job_id, "processing" if processed + errors < len(filenames) else "done",
                                       processed_files=processed, error_count=errors)

    final_status = "done"
    if errors > 0 and processed == 0:
        final_status = "failed"
    elif errors > 0:
        final_status = "done"

    await db.update_job_status(job_id, final_status, processed_files=processed, error_count=errors)
