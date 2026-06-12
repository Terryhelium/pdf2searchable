from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.db import Database
from app.ocr import OCRProcessor

logger = logging.getLogger(__name__)


def _pick_result(results: dict[str, list[str]]) -> str:
    """从多格式输出中选一个主路径存储（用于下载链接）"""
    for fmt in ("pdf", "tiff", "jpeg", "txt", "md", "json"):
        paths = results.get(fmt)
        if paths:
            return paths[0]
    return ""


async def process_single_file(db: Database, ocr: OCRProcessor,
                              job_id: str, file_path: Path, output_dir: Path,
                              filename: Optional[str] = None):
    """处理单个文件（单文件上传模式用）"""
    fname = filename or file_path.name
    try:
        await db.update_job_status(job_id, "processing")
        await db.add_job_files(job_id, [fname])
        results = await ocr.process(str(file_path), str(output_dir))
        main_path = _pick_result(results)
        await db.update_file_status(job_id, fname, "done", result_path=main_path)
        await db.update_job_status(job_id, "done", processed_files=1)
        logger.info("File processed: %s -> %s", file_path, results)
    except Exception as e:
        logger.exception("File processing failed: %s", file_path)
        err_msg = str(e)
        await db.update_file_status(job_id, fname, "failed", error_msg=err_msg)
        await db.update_job_status(job_id, "failed", processed_files=0, error_count=1)


async def run_batch_job(db: Database, ocr: OCRProcessor,
                        job_id: str, source_dir: str, dest_dir: str):
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
    await db.add_job_files(job_id, filenames)

    processed = 0
    errors = 0

    for filename in filenames:
        file_path = src / filename
        try:
            results = await ocr.process(str(file_path), str(dst))
            main_path = _pick_result(results)
            await db.update_file_status(job_id, filename, "done", result_path=main_path)
            processed += 1
        except Exception as e:
            logger.error("Batch file failed: %s - %s", filename, e)
            await db.update_file_status(job_id, filename, "failed", error_msg=str(e))
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
