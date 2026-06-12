from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import httpx

from app.config import Settings
from app.formatters import registry as formatter_registry

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, service: str, status_code: int, detail: str):
        self.service = service
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{service}] {status_code}: {detail}")


class PaddleOCRClient:
    def __init__(self, settings: Settings):
        self.url = settings.paddleocr_url.rstrip("/")
        self.timeout = settings.paddleocr_timeout

    async def ocr(self, file_path: str) -> dict:
        url = f"{self.url}/ocr"
        logger.info("PaddleOCR: POST %s (file=%s)", url, file_path)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with open(file_path, "rb") as f:
                    resp = await client.post(url, files={"file": f})
                if resp.is_error:
                    raise ServiceError("PaddleOCR", resp.status_code, resp.text)
                return resp.json()
        except httpx.TimeoutException:
            raise ServiceError("PaddleOCR", 0, "timeout")
        except httpx.ConnectError:
            raise ServiceError("PaddleOCR", 0, "connection refused")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.url}/")
                return resp.status_code < 500
        except Exception:
            return False


class MinerUClient:
    def __init__(self, settings: Settings):
        self.url = settings.mineru_url.rstrip("/")
        self.timeout = settings.mineru_timeout

    async def parse(self, file_path: str) -> dict:
        url = f"{self.url}/api/v1/parse"
        logger.info("MinerU: POST %s (file=%s)", url, file_path)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with open(file_path, "rb") as f:
                    resp = await client.post(url, files={"file": f})
                if resp.is_error:
                    raise ServiceError("MinerU", resp.status_code, resp.text)
                return resp.json()
        except httpx.TimeoutException:
            raise ServiceError("MinerU", 0, "timeout")
        except httpx.ConnectError:
            raise ServiceError("MinerU", 0, "connection refused")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.url}/")
                return resp.status_code < 500
        except Exception:
            return False


class OCRProcessor:
    """协调 OCR 引擎 + 多格式输出"""

    # 各格式依赖的 OCR 引擎
    _ENGINE_REQUIREMENTS = {
        "pdf": {"paddleocr"},   # 需要精确文字坐标做覆盖层
        "md": {"mineru"},       # 需要结构化文档解析
        "txt": {"mineru"},      # 需要阅读顺序
        "json": {"paddleocr", "mineru"},  # 全量数据
        "tiff": set(),          # 纯图像转换，不需要OCR
        "jpeg": set(),          # 纯图像转换，不需要OCR
    }

    def __init__(self, paddleocr: PaddleOCRClient, mineru: MinerUClient):
        self.paddleocr = paddleocr
        self.mineru = mineru

    async def process(self, file_path: str, output_root: str, formats: Optional[list[str]] = None) -> dict[str, list[str]]:
        """
        对文件执行 OCR 并生成指定格式的输出文件。

        Args:
            file_path: 输入文件路径
            output_root: 输出根目录（各格式自动创建子目录）
            formats: 需要的输出格式列表

        Returns:
            {format: [output_path, ...]} 字典
        """
        if formats is None:
            formats = ["pdf"]

        input_path = Path(file_path)
        root = Path(output_root)

        # 1. 按需调用 OCR 引擎
        needed_engines: set[str] = set()
        for fmt in formats:
            needed_engines |= self._ENGINE_REQUIREMENTS.get(fmt, set())

        ocr_data: dict = {}
        if "paddleocr" in needed_engines:
            ocr_data["paddleocr"] = await self.paddleocr.ocr(file_path)
        if "mineru" in needed_engines:
            ocr_data["mineru"] = await self.mineru.parse(file_path)

        # 2. 各格式写入独立子目录
        results: dict[str, list[str]] = {}
        for fmt in formats:
            fmt_dir = root / fmt
            fmt_dir.mkdir(parents=True, exist_ok=True)

            formatter_cls = formatter_registry.get(fmt)
            if not formatter_cls:
                logger.warning("Unknown format: %s, skipping", fmt)
                continue
            formatter = formatter_cls(ocr_data)
            paths = await formatter.format(input_path, fmt_dir, ocr_data)
            results[fmt] = [str(p) for p in paths]
            logger.info("Generated %s: %s", fmt, paths)

        return results
