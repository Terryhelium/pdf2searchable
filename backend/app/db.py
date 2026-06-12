from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from app.config import Settings


class Database:
    def __init__(self, settings: Settings):
        self.path = settings.database_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._init_tables()

    async def _init_tables(self):
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                source_dir TEXT,
                dest_dir TEXT,
                total_files INTEGER DEFAULT 0,
                processed_files INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                formats TEXT DEFAULT 'pdf,txt,md',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS job_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                error_msg TEXT,
                result_path TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            );
        """)
        # 兼容旧表（无 formats 列时补齐）
        try:
            await self._conn.execute("ALTER TABLE jobs ADD COLUMN formats TEXT DEFAULT 'pdf,txt,md'")
            await self._conn.commit()
        except Exception:
            pass  # 列已存在

    async def close(self):
        if self._conn:
            await self._conn.close()

    # ── Stats ──

    async def get_stats(self) -> dict:
        cursor = await self._conn.execute("""
            SELECT
                COALESCE(COUNT(*), 0) as total_jobs,
                COALESCE(SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END), 0) as success_jobs,
                COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed_jobs,
                COALESCE(SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END), 0) as processing_jobs,
                COALESCE(SUM(CASE WHEN date(created_at) = date('now') THEN 1 ELSE 0 END), 0) as today_jobs,
                COALESCE(SUM(COALESCE(total_files, 0)), 0) as total_files
            FROM jobs
        """)
        row = await cursor.fetchone()
        return dict(row) if row else {
            "total_jobs": 0, "success_jobs": 0, "failed_jobs": 0,
            "processing_jobs": 0, "today_jobs": 0, "total_files": 0,
        }

    # ── Jobs ──

    async def create_job(self, job_type: str, source_dir: Optional[str] = None,
                         dest_dir: Optional[str] = None, formats: Optional[list[str]] = None) -> str:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        fmts = ",".join(formats) if formats else "pdf,txt,md"
        await self._conn.execute(
            "INSERT INTO jobs (id, type, status, source_dir, dest_dir, formats, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, job_type, "pending", source_dir, dest_dir, fmts, now, now),
        )
        await self._conn.commit()
        return job_id

    async def update_job_status(self, job_id: str, status: str,
                                processed_files: Optional[int] = None,
                                error_count: Optional[int] = None,
                                total_files: Optional[int] = None):
        now = datetime.now(timezone.utc).isoformat()
        parts = ["updated_at = ?"]
        params: list = [now]
        if status:
            parts.append("status = ?")
            params.append(status)
        if processed_files is not None:
            parts.append("processed_files = ?")
            params.append(processed_files)
        if error_count is not None:
            parts.append("error_count = ?")
            params.append(error_count)
        if total_files is not None:
            parts.append("total_files = ?")
            params.append(total_files)
        params.append(job_id)
        await self._conn.execute(
            f"UPDATE jobs SET {', '.join(parts)} WHERE id = ?", params
        )
        await self._conn.commit()

    async def get_job(self, job_id: str) -> Optional[dict]:
        cursor = await self._conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_jobs(self, limit: int = 50) -> list[dict]:
        cursor = await self._conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ── Job Files ──

    async def add_job_files(self, job_id: str, filenames: list[str]):
        await self._conn.executemany(
            "INSERT INTO job_files (job_id, filename, status) VALUES (?, ?, 'pending')",
            [(job_id, f) for f in filenames],
        )
        await self._conn.commit()

    async def update_file_status(self, job_id: str, filename: str, status: str,
                                 error_msg: Optional[str] = None,
                                 result_path: Optional[str] = None):
        await self._conn.execute(
            "UPDATE job_files SET status = ?, error_msg = ?, result_path = ? WHERE job_id = ? AND filename = ?",
            (status, error_msg, result_path, job_id, filename),
        )
        await self._conn.commit()

    async def get_job_files(self, job_id: str) -> list[dict]:
        cursor = await self._conn.execute(
            "SELECT * FROM job_files WHERE job_id = ? ORDER BY id", (job_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
