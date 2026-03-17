"""
异常定义模块
提供上传相关的异常类型
"""

from __future__ import annotations


class UploadError(Exception):
    """上传失败异常基类"""
    pass


class UploadInitError(UploadError):
    """上传初始化失败"""
    pass


class UploadFinishError(UploadError):
    """上传完成失败"""
    pass


class ChunkUploadError(UploadError):
    """分片上传失败"""
    def __init__(self, chunk_index: int, attempts: int, message: str):
        self.chunk_index = chunk_index
        self.attempts = attempts
        super().__init__(f"Chunk {chunk_index} failed after {attempts} attempts: {message}")
