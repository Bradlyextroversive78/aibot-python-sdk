"""配置相关类型定义"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, Any


class Logger(Protocol):
    """日志接口协议"""

    def debug(self, message: str, *args: Any) -> None: ...
    def info(self, message: str, *args: Any) -> None: ...
    def warn(self, message: str, *args: Any) -> None: ...
    def error(self, message: str, *args: Any) -> None: ...


@dataclass
class WSClientOptions:
    """WSClient 配置选项"""

    # 机器人 ID（在企业微信后台获取）
    bot_id: str
    # 机器人 Secret（在企业微信后台获取）
    secret: str
    # WebSocket 重连基础延迟（毫秒），实际延迟按指数退避递增，默认 1000
    reconnect_interval: int = 1000
    # 最大重连次数，默认 10，设为 -1 表示无限重连
    max_reconnect_attempts: int = 10
    # 心跳间隔（毫秒），默认 30000
    heartbeat_interval: int = 30000
    # 请求超时时间（毫秒），默认 10000
    request_timeout: int = 10000
    # 自定义 WebSocket 连接地址，默认 wss://openws.work.weixin.qq.com
    ws_url: str = "wss://openws.work.weixin.qq.com"
    # 自定义日志函数
    logger: Logger | None = None
