from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request, Query
from fastapi.responses import FileResponse, JSONResponse

from app.config import Settings, load_settings
from app.db import Database
from app.models import (
    BatchCreateRequest, BatchCreateResponse, BatchDetailResponse,
    BatchJobInfo, BatchListResponse, FileDownloadInfo, HealthResponse,
    StatsResponse, UploadResponse, OUTPUT_FORMATS, OUTPUT_FORMAT_LABELS,
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


# ── 目录浏览 ──

@app.get("/api/browse")
async def browse_directory(path: str = Query("/", description="浏览的目录路径")):
    """列出指定目录的内容（用于批量处理的目录选择器）"""
    try:
        p = Path(path).resolve()
        if not p.is_dir():
            # 尝试从父目录开始
            p = p.parent.resolve()
        if not p.exists():
            p = Path("/")

        items = []
        for entry in sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            try:
                items.append({
                    "name": entry.name,
                    "path": str(entry.resolve()),
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else 0,
                })
            except PermissionError:
                continue

        return {
            "current": str(p.resolve()),
            "parent": str(p.parent.resolve()) if p.parent != p else None,
            "items": items,
        }
    except Exception as e:
        raise HTTPException(400, detail=str(e))


# ── 单文件上传 ──

@app.post("/api/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
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
    ocr = app.state.ocr
    job_id = await db.create_job("single", formats=fmt_list)

    # 同步处理（等待完成）
    output_dir = upload_dir / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    await process_single_file(db, ocr, job_id, file_path, output_dir, file.filename, fmt_list)

    # 查询结果
    job = await db.get_job(job_id)
    files = await db.get_job_files(job_id)
    error = None
    file_list = []
    if job["status"] == "done":
        for f in files:
            fmt = Path(f["result_path"]).parent.name if f.get("result_path") else ""
            label = OUTPUT_FORMAT_LABELS.get(fmt, fmt.upper())
            file_list.append(FileDownloadInfo(
                format=fmt,
                label=label,
                url=f"/api/download/{job_id}?format={fmt}",
            ))
    elif job["status"] == "failed":
        error = files[0].get("error_msg") if files else "处理失败"

    return UploadResponse(
        job_id=job_id,
        status=job["status"],
        formats=fmt_list,
        files=file_list,
        error=error,
    )


@app.get("/api/jobs/{job_id}", response_model=UploadResponse)
async def get_job(job_id: str):
    db = app.state.db
    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(404, detail="job not found")
    error = None
    file_list = []
    job_files = await db.get_job_files(job_id)
    if job["status"] == "done":
        for f in job_files:
            fmt = f.get("format") or (Path(f["result_path"]).parent.name if f.get("result_path") else "")
            if fmt:
                label = OUTPUT_FORMAT_LABELS.get(fmt, fmt.upper())
                file_list.append(FileDownloadInfo(
                    format=fmt,
                    label=label,
                    url=f"/api/download/{job_id}?format={fmt}",
                ))
    elif job["status"] == "failed" and job_files:
        error = job_files[0].get("error_msg")

    fmts = job.get("formats", "pdf,txt,md").split(",") if job.get("formats") else []

    return UploadResponse(
        job_id=job["id"],
        status=job["status"],
        formats=fmts,
        files=file_list,
        error=error,
    )


# ── 删除任务 ──

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """删除单个任务及其结果文件"""
    db = app.state.db
    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(404, detail="job not found")
    paths = await db.delete_job(job_id)
    for p in paths:
        try:
            os.remove(p)
        except Exception:
            pass
    return {"deleted": job_id}


@app.delete("/api/jobs")
async def batch_delete_jobs(job_ids: list[str] = Query(..., description="任务ID列表")):
    """批量删除任务及其结果文件"""
    db = app.state.db
    paths = await db.delete_jobs(job_ids)
    for p in paths:
        try:
            os.remove(p)
        except Exception:
            pass
    return {"deleted": job_ids, "count": len(job_ids)}


# ── 文件下载 ──

@app.get("/api/download/{job_id}")
async def download_file(job_id: str, format: str = ""):
    db = app.state.db
    job_files = await db.get_job_files(job_id)
    if format:
        # 按格式下载
        for f in job_files:
            if f.get("result_path") and Path(f["result_path"]).parent.name == format:
                return FileResponse(f["result_path"], filename=Path(f["result_path"]).name)
        raise HTTPException(404, detail=f"format not found: {format}")
    # 回退：下载第一个结果文件
    for f in job_files:
        if f.get("result_path"):
            return FileResponse(f["result_path"], filename=Path(f["result_path"]).name)
    raise HTTPException(404, detail="file not found")


# ── 批量处理 ──

@app.post("/api/batch/upload-files", status_code=201)
async def batch_upload_files(files: list[UploadFile] = File(...)):
    """上传多个文件到临时目录，返回目录路径用于批量处理"""
    if not files:
        raise HTTPException(400, detail="请选择至少一个文件")

    batch_dir = Path(settings.upload_dir) / "batch_uploads" / uuid.uuid4().hex
    batch_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for file in files:
        if not file.filename:
            continue
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = batch_dir / safe_name
        content = await file.read()
        file_path.write_bytes(content)
        saved.append(file.filename)

    if not saved:
        raise HTTPException(400, detail="没有成功保存任何文件")

    return {
        "source_dir": str(batch_dir),
        "files": saved,
        "count": len(saved),
    }


@app.post("/api/batch", response_model=BatchCreateResponse, status_code=201)
async def create_batch(req: BatchCreateRequest, background_tasks: BackgroundTasks = None):
    src = Path(req.source_dir)
    if not src.is_dir():
        raise HTTPException(400, detail=f"source_dir not found: {req.source_dir}")

    db = app.state.db
    job_id = await db.create_job("batch", source_dir=req.source_dir, dest_dir=req.dest_dir, formats=req.formats)

    background_tasks.add_task(run_batch_job, db, app.state.ocr, job_id, req.source_dir, req.dest_dir, req.formats)

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
