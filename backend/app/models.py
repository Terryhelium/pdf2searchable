from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# 输出格式定义
OUTPUT_FORMATS = ["pdf", "tiff", "jpeg", "txt", "md", "json"]
OUTPUT_FORMAT_LABELS = {
    "pdf": "可搜索PDF",
    "tiff": "TIFF图像",
    "jpeg": "JPEG预览",
    "txt": "纯文本",
    "md": "Markdown",
    "json": "JSON结构化数据",
}


# ── 统计 ──

class StatsResponse(BaseModel):
    total_jobs: int = 0
    success_jobs: int = 0
    failed_jobs: int = 0
    processing_jobs: int = 0
    today_jobs: int = 0
    total_files: int = 0


# ── 单文件上传 ──

class FileDownloadInfo(BaseModel):
    format: str
    label: str
    url: str


class UploadResponse(BaseModel):
    job_id: str
    status: str
    formats: list[str] = []
    files: list[FileDownloadInfo] = []
    error: Optional[str] = None


# ── 批量处理 ──

class BatchCreateRequest(BaseModel):
    source_dir: str
    dest_dir: str
    file_pattern: str = "*"
    formats: list[str] = Field(default_factory=lambda: ["pdf", "txt", "md"])


class BatchCreateResponse(BaseModel):
    job_id: str
    status: str
    total_files: int = 0
    formats: list[str] = []


class BatchJobInfo(BaseModel):
    job_id: str
    type: str
    status: str
    source_dir: Optional[str] = None
    dest_dir: Optional[str] = None
    total_files: int = 0
    processed_files: int = 0
    error_count: int = 0
    formats: list[str] = []
    created_at: str = ""
    updated_at: str = ""


class BatchFileInfo(BaseModel):
    filename: str
    status: str
    error_msg: Optional[str] = None
    result_path: Optional[str] = None


class BatchDetailResponse(BaseModel):
    job_id: str
    status: str
    total_files: int
    processed_files: int
    error_count: int
    formats: list[str] = []
    created_at: str
    updated_at: str
    files: list[BatchFileInfo] = []


class BatchListResponse(BaseModel):
    jobs: list[BatchJobInfo] = []


# ── 健康检查 ──

class HealthResponse(BaseModel):
    status: str
    paddleocr: str
    mineru: str


# ── 通用 ──

class ErrorResponse(BaseModel):
    detail: str
