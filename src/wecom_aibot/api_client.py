"""
企业微信 API 客户端
仅负责文件下载等 HTTP 辅助功能，消息收发均走 WebSocket 通道
"""

from __future__ import annotations
from typing import Any
import httpx

from wecom_aibot.types import Logger
from wecom_aibot.crypto import decrypt_file
from wecom_aibot.logger import DefaultLogger


class WeComApiClient:
    """
    企业微信 API 客户端

    负责 HTTP 相关操作，主要是文件下载和解密
    """

    DEFAULT_TIMEOUT = 30000  # 30秒

    def __init__(self, logger: Logger | None = None, timeout: int = DEFAULT_TIMEOUT):
        self.logger = logger or DefaultLogger()
        self.timeout = timeout / 1000  # 转换为秒
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def download_file_raw(self, url: str) -> tuple[bytes, str | None]:
        """
        下载文件（返回原始 bytes 及文件名）

        Args:
            url: 文件下载地址

        Returns:
            (文件内容, 文件名) 元组
        """
        client = await self._get_client()

        self.logger.debug(f"正在下载文件: {url}")
        response = await client.get(url)
        response.raise_for_status()

        # 从 Content-Disposition 头获取文件名
        filename = None
        content_disposition = response.headers.get("content-disposition")
        if content_disposition:
            # 解析 filename="xxx" 或 filename*=UTF-8''xxx
            import re

            match = re.search(r'filename\*?=["\']?(?:UTF-8\'\')?([^"\';]+)', content_disposition)
            if match:
                from urllib.parse import unquote

                filename = unquote(match.group(1))

        return response.content, filename

    async def download_file(self, url: str, aes_key: str | None = None) -> tuple[bytes, str | None]:
        """
        下载文件并使用 AES 密钥解密

        Args:
            url: 文件下载地址
            aes_key: AES 解密密钥（Base64 编码），取自消息中 image.aeskey 或 file.aeskey 字段

        Returns:
            (解密后的文件内容, 文件名) 元组
        """
        buffer, filename = await self.download_file_raw(url)

        if aes_key:
            self.logger.debug("正在解密文件...")
            buffer = decrypt_file(buffer, aes_key)

        return buffer, filename
