from __future__ import annotations

import asyncio
import base64
import json
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
    """PaddleOCR-VL API 客户端 (port 8080)

    API:
      POST /layout-parsing  JSON body (base64 编码文件)
      GET  /health
    """

    def __init__(self, settings: Settings):
        self.url = settings.paddleocr_url.rstrip("/")
        self.timeout = settings.paddleocr_timeout

    async def ocr(self, file_path: str) -> dict:
        url = f"{self.url}/layout-parsing"
        logger.info("PaddleOCR: POST %s (file=%s)", url, file_path)

        ext = Path(file_path).suffix.lower()
        file_type = 0 if ext == ".pdf" else 1

        if ext == ".pdf":
            # 用 PyMuPDF 统一渲染 PDF 各页为 PNG（144 DPI），确保坐标对齐
            import fitz
            import io
            src = fitz.open(file_path)
            zoom = 144.0 / 72.0  # 2x
            all_results = []
            for pi in range(len(src)):
                page = src[pi]
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                img_data = pix.tobytes("png")

                # 逐页发送给 PaddleOCR
                b64 = base64.b64encode(img_data).decode()
                payload = {"file": b64, "fileType": 1, "useLayoutDetection": True}
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.post(url, json=payload)
                        if resp.is_error:
                            raise ServiceError("PaddleOCR", resp.status_code, resp.text)
                        result = resp.json()
                    # 合并各页结果，修正宽高为实际渲染尺寸
                    page_result = result.get("result", {}).get("layoutParsingResults", [])
                    for pr in page_result:
                        pruned = pr.get("prunedResult", {})
                        pruned["width"] = pix.width
                        pruned["height"] = pix.height
                    all_results.extend(page_result)
                except Exception as e:
                    logger.warning("第%d页OCR失败: %s", pi, e)
                    continue

            page_count = len(src)
            src.close()
            file_type = 1
            file_data = b""  # 不再发送原文件
            result = {
                "errorCode": 0,
                "errorMsg": "Success",
                "result": {"layoutParsingResults": all_results},
            }
            logger.info("PaddleOCR: PDF %d页全部渲染识别完成", page_count)
            return result
        else:
            with open(file_path, "rb") as f:
                file_data = f.read()

        payload = {
            "file": base64.b64encode(file_data).decode(),
            "fileType": file_type,
            "useLayoutDetection": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.is_error:
                    raise ServiceError("PaddleOCR", resp.status_code, resp.text)
                result = resp.json()
                if result.get("errorCode", 0) != 0:
                    raise ServiceError("PaddleOCR", 200, result.get("errorMsg", "unknown error"))
                return result
        except httpx.TimeoutException:
            raise ServiceError("PaddleOCR", 0, "timeout")
        except httpx.ConnectError:
            raise ServiceError("PaddleOCR", 0, "connection refused")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.url}/health")
                if resp.is_error:
                    return False
                data = resp.json()
                return data.get("errorCode", -1) == 0
        except Exception:
            return False


class MinerUClient:
    """MinerU API 客户端 (port 8000)

    API:
      POST /file_parse      multipart/form-data 文件上传
      GET  /health
      GET  /tasks/{task_id}  任务状态查询
    """

    def __init__(self, settings: Settings):
        self.url = settings.mineru_url.rstrip("/")
        self.timeout = settings.mineru_timeout

    async def parse(self, file_path: str) -> dict:
        url = f"{self.url}/file_parse"
        logger.info("MinerU: POST %s (file=%s)", url, file_path)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with open(file_path, "rb") as f:
                    resp = await client.post(
                        url,
                        files={"files": f},
                        data={
                            "backend": "pipeline",
                            "return_md": True,
                            "return_content_list": True,
                            "return_middle_json": True,
                        },
                    )
                if resp.is_error:
                    raise ServiceError("MinerU", resp.status_code, resp.text)

                result = resp.json()

                # 任务式响应：如果状态不是 completed，轮询等待
                if result.get("status") not in ("completed", "failed"):
                    task_id = result["task_id"]
                    result = await self._poll_result(client, task_id)
                elif result.get("status") == "failed":
                    raise ServiceError("MinerU", 0, result.get("error", "task failed"))

                return self._normalize_result(file_path, result)

        except httpx.TimeoutException:
            raise ServiceError("MinerU", 0, "timeout")
        except httpx.ConnectError:
            raise ServiceError("MinerU", 0, "connection refused")

    async def _poll_result(self, client: httpx.AsyncClient, task_id: str) -> dict:
        status_url = f"{self.url}/tasks/{task_id}"
        result_url = f"{self.url}/tasks/{task_id}/result"

        poll_interval = 2
        max_attempts = max(1, self.timeout // poll_interval)

        for _ in range(max_attempts):
            await asyncio.sleep(poll_interval)
            resp = await client.get(status_url)
            if resp.is_error:
                raise ServiceError("MinerU", resp.status_code, f"task status failed: {task_id}")
            data = resp.json()
            if data.get("status") == "completed":
                r = await client.get(result_url)
                if r.is_error:
                    raise ServiceError("MinerU", r.status_code, f"task result failed: {task_id}")
                return r.json()
            elif data.get("status") == "failed":
                raise ServiceError("MinerU", 0, data.get("error", "task failed"))

        raise ServiceError("MinerU", 0, f"task timeout: {task_id}")

    def _normalize_result(self, file_path: str, raw: dict) -> dict:
        """统一返回格式：按文件名提取结果，解析内嵌 JSON 字符串"""
        fname = Path(file_path).name
        results = raw.get("results") or {}
        file_result = results.get(fname, {})

        # content_list 和 middle_json 是内嵌 JSON 字符串，需要解析
        for key in ("content_list", "middle_json"):
            val = file_result.get(key)
            if isinstance(val, str) and val:
                try:
                    file_result[key] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass

        return file_result

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.url}/health")
                return resp.status_code < 500
        except Exception:
            return False


class OCRProcessor:
    """协调 OCR 引擎调用 + 多格式输出"""

    _ENGINE_REQUIREMENTS = {
        "pdf": {"paddleocr"},        # 精确文字坐标做 PDF 文字覆盖层
        "md": {"mineru"},            # MinerU 结构化 markdown 输出
        "txt": {"mineru"},           # MinerU 阅读顺序提取纯文本
        "json": {"paddleocr", "mineru"},  # 全量数据
        "tiff": set(),               # 纯图像转换
        "jpeg": set(),               # 纯图像转换
    }

    def __init__(self, paddleocr: PaddleOCRClient, mineru: MinerUClient):
        self.paddleocr = paddleocr
        self.mineru = mineru

    async def process(
        self,
        file_path: str,
        output_root: str,
        formats: Optional[list[str]] = None,
    ) -> dict[str, list[str]]:
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
                logger.warning("未知格式: %s，跳过", fmt)
                continue
            formatter = formatter_cls(ocr_data)
            paths = await formatter.format(input_path, fmt_dir, ocr_data)
            results[fmt] = [str(p) for p in paths]
            logger.info("已生成 %s: %s", fmt, paths)

        return results
