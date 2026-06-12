from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseFormatter(ABC):
    """输出格式生成器基类"""

    name: str  # 格式标识，如 "pdf", "txt", "md"

    @abstractmethod
    async def format(self, input_path: Path, output_dir: Path, ocr_data: dict) -> list[Path]:
        """
        生成格式化的输出文件。

        Args:
            input_path: 原始输入文件路径（用于取文件名 stem）
            output_dir: 该格式独立的输出目录（如 dest/pdf/）
            ocr_data: OCR 引擎返回的完整数据

        Returns:
            生成的文件路径列表（多数格式返回1个，JPEG按页返回多个）
        """
        ...


class FormatterRegistry(dict[str, type[BaseFormatter]]):
    """格式注册表"""

    def register(self, cls: type[BaseFormatter]) -> type[BaseFormatter]:
        assert cls.name, f"{cls.__name__}.name is not set"
        self[cls.name] = cls
        return cls

    def build_all(self, formats: list[str], ocr_data: dict) -> list[BaseFormatter]:
        """根据格式列表构造实例"""
        result = []
        for fmt in formats:
            cls = self.get(fmt)
            if cls:
                result.append(cls(ocr_data))
        return result


# 全局注册表
registry = FormatterRegistry()
