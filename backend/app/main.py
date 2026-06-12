from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse

from app.config import Settings, load_settings
from app.db import Database
from app.models import (
    BatchCreateRequest, BatchCreateResponse, BatchDetailResponse,
    BatchJobInfo, BatchListResponse, ErrorResponse, HealthResponse,
    StatsResponse, UploadResponse, OUTPUT_FORMATS,
)
from app.ocr import PaddleOCRClient, MinerUClient, OCRProcessor, ServiceError
from app.tasks import process_single_file, run_batch_job

logger = logging.getLogger(__name__)

settings: Settings = load_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    db = Database(settings)
    await db.connect()
    app.state.db = db

    paddleocr = PaddleOCRClient(settings)
    mineru = MinerUClient(settings)
    app.state.ocr = OCRProcessor(paddleocr, mineru)

    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info("OCR系统 started on port %d", settings.backend_port)
    yield
    # shutdown
    await db.close()


app = FastAPI(
    title="宁波市档案馆文档OCR处理系统",
    version="0.2.0",
    lifespan=lifespan,
)


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return JSONResponse(
        status_code=exc.status_code or 502,
        content={"detail": f"{exc.service}: {exc.detail}"},
    )


# ── 统计 ──

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    db = app.state.db
    return await db.get_stats()


# ── 健康检查 ──

@app.get("/api/health", response_model=HealthResponse)
async def health():
    paddleocr = app.state.ocr.paddleocr
    mineru = app.state.ocr.mineru
    po_ok = await paddleocr.health()
    mu_ok = await mineru.health()
    return HealthResponse(
        status="ok" if po_ok or mu_ok else "degraded",
        paddleocr="ok" if po_ok else "error",
        mineru="ok" if mu_ok else "error",
    )


# ── 单文件上传 ──

@app.post("/api/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    formats: str = "pdf,txt,md",
):
    if not file.filename:
        raise HTTPException(400, detail="filename required")

    fmt_list = [f.strip() for f in formats.split(",") if f.strip() in OUTPUT_FORMATS]
    if not fmt_list:
        fmt_list = ["pdf"]

    # 保存上传文件
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = upload_dir / safe_name

    content = await file.read()
    file_path.write_bytes(content)

    # 创建任务
    db = app.state.db
    job_id = await db.create_job("single", formats=fmt_list)

    # 后台处理
    output_dir = upload_dir / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    background_tasks.add_task(process_single_file, db, app.state.ocr, job_id, file_path, output_dir, file.filename)

    return UploadResponse(job_id=job_id, status="pending", formats=fmt_list)


@app.get("/api/jobs/{job_id}", response_model=UploadResponse)
async def get_job(job_id: str):
    db = app.state.db
    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(404, detail="job not found")
    result_url = None
    error = None
    if job["status"] == "done":
        files = await db.get_job_files(job_id)
        if files:
            result_url = f"/api/download/{job_id}/{files[0]['filename']}"
    elif job["status"] == "failed":
        files = await db.get_job_files(job_id)
        if files:
            error = files[0].get("error_msg")

    fmts = job.get("formats", "pdf,txt,md").split(",") if job.get("formats") else []

    return UploadResponse(
        job_id=job["id"],
        status=job["status"],
        formats=fmts,
        result_url=result_url,
        error=error,
    )


# ── 文件下载 ──

@app.get("/api/download/{job_id}/{filename:path}")
async def download_file(job_id: str, filename: str):
    db = app.state.db
    files = await db.get_job_files(job_id)
    for f in files:
        if f["filename"] == filename and f.get("result_path"):
            return FileResponse(f["result_path"], filename=filename)
    raise HTTPException(404, detail="file not found")


# ── 批量处理 ──

@app.post("/api/batch", response_model=BatchCreateResponse, status_code=201)
async def create_batch(req: BatchCreateRequest, background_tasks: BackgroundTasks = None):
    src = Path(req.source_dir)
    if not src.is_dir():
        raise HTTPException(400, detail=f"source_dir not found: {req.source_dir}")

    db = app.state.db
    job_id = await db.create_job("batch", source_dir=req.source_dir, dest_dir=req.dest_dir, formats=req.formats)

    background_tasks.add_task(run_batch_job, db, app.state.ocr, job_id, req.source_dir, req.dest_dir)

    return BatchCreateResponse(job_id=job_id, status="pending", formats=req.formats)


@app.get("/api/batch/{job_id}", response_model=BatchDetailResponse)
async def get_batch_detail(job_id: str):
    db = app.state.db
    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(404, detail="job not found")
    files = await db.get_job_files(job_id)
    fmts = job.get("formats", "pdf,txt,md").split(",") if job.get("formats") else []
    return BatchDetailResponse(
        job_id=job["id"],
        status=job["status"],
        total_files=job["total_files"],
        processed_files=job["processed_files"],
        error_count=job["error_count"],
        formats=fmts,
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        files=[{"filename": f["filename"], "status": f["status"],
                "error_msg": f.get("error_msg"), "result_path": f.get("result_path")}
               for f in files],
    )


@app.get("/api/batch", response_model=BatchListResponse)
async def list_batches():
    db = app.state.db
    jobs = await db.list_jobs()
    batch_jobs = [BatchJobInfo(
        job_id=j["id"], type=j["type"], status=j["status"],
        source_dir=j.get("source_dir"), dest_dir=j.get("dest_dir"),
        total_files=j["total_files"], processed_files=j["processed_files"],
        error_count=j["error_count"],
        formats=j.get("formats", "pdf,txt,md").split(",") if j.get("formats") else [],
        created_at=j["created_at"], updated_at=j["updated_at"],
    ) for j in jobs]
    return BatchListResponse(jobs=batch_jobs)
