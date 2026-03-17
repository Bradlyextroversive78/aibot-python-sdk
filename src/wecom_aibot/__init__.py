"""
企业微信智能机器人 Python SDK

提供 WebSocket 长连接通道，支持消息收发、事件回调、流式回复等功能。
"""

from wecom_aibot.client import WSClient
from wecom_aibot.logger import DefaultLogger
from wecom_aibot.types import (
    MessageType,
    EventType,
    TemplateCardType,
    WSClientOptions,
    WsFrame,
    Logger,
    # 媒体上传类型
    WeComMediaType,
    VideoOptions,
    UploadMediaOptions,
    UploadMediaFinishResult,
)
from wecom_aibot.exceptions import (
    UploadError,
    UploadInitError,
    UploadFinishError,
    ChunkUploadError,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    "WSClient",
    # Logger
    "DefaultLogger",
    # Enums
    "MessageType",
    "EventType",
    "TemplateCardType",
    # Types
    "WSClientOptions",
    "WsFrame",
    "Logger",
    # Media upload types
    "WeComMediaType",
    "VideoOptions",
    "UploadMediaOptions",
    "UploadMediaFinishResult",
    # Exceptions
    "UploadError",
    "UploadInitError",
    "UploadFinishError",
    "ChunkUploadError",
]
