"""
WebSocket 连接管理器
负责 WebSocket 连接、心跳、重连、消息发送
"""

from __future__ import annotations
import asyncio
import json
from typing import Any, Callable
from dataclasses import dataclass, field
import websockets
from websockets.asyncio.client import ClientConnection

from wecom_aibot.types import WsFrame, Logger
from wecom_aibot.types.api import WsCmd
from wecom_aibot.utils import generate_req_id
from wecom_aibot.logger import DefaultLogger


@dataclass
class PendingAck:
    """等待回执的消息"""

    future: asyncio.Future
    timer: asyncio.Task | None = None


@dataclass
class ReplyQueueItem:
    """回复队列项"""

    body: Any
    cmd: str
    future: asyncio.Future


class WsConnectionManager:
    """
    WebSocket 连接管理器

    负责：
    - WebSocket 连接建立与断开
    - 心跳保持与断线检测
    - 自动重连（指数退避）
    - 认证
    - 消息发送与回执等待
    - 回复队列管理（同一 req_id 串行发送）
    """

    # 默认配置
    DEFAULT_WS_URL = "wss://openws.work.weixin.qq.com"
    DEFAULT_HEARTBEAT_INTERVAL = 30000  # 30秒
    DEFAULT_RECONNECT_BASE_DELAY = 1000  # 1秒
    DEFAULT_MAX_RECONNECT_ATTEMPTS = 10
    MAX_MISSED_PONG = 3
    RECONNECT_MAX_DELAY = 60000  # 60秒
    REPLY_ACK_TIMEOUT = 10000  # 10秒
    MAX_REPLY_QUEUE_SIZE = 100

    def __init__(
        self,
        logger: Logger | None = None,
        heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
        reconnect_base_delay: int = DEFAULT_RECONNECT_BASE_DELAY,
        max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS,
        ws_url: str = DEFAULT_WS_URL,
    ):
        self.logger = logger or DefaultLogger()
        self.ws_url = ws_url
        self.heartbeat_interval = heartbeat_interval / 1000  # 转换为秒
        self.reconnect_base_delay = reconnect_base_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        # WebSocket 连接
        self._ws: ClientConnection | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._receive_task: asyncio.Task | None = None

        # 认证凭证
        self._bot_id: str | None = None
        self._bot_secret: str | None = None

        # 连接状态
        self._is_manual_close = False
        self._reconnect_attempts = 0
        self._missed_pong_count = 0
        self._is_connected = False
        self._is_authenticated = False

        # 回复队列管理
        self._reply_queues: dict[str, list[ReplyQueueItem]] = {}
        self._pending_acks: dict[str, PendingAck] = {}

        # 回调函数
        self.on_connected: Callable[[], None] | None = None
        self.on_authenticated: Callable[[], None] | None = None
        self.on_disconnected: Callable[[str], None] | None = None
        self.on_message: Callable[[WsFrame], None] | None = None
        self.on_reconnecting: Callable[[int], None] | None = None
        self.on_error: Callable[[Exception], None] | None = None

    def set_credentials(self, bot_id: str, bot_secret: str) -> None:
        """设置认证凭证"""
        self._bot_id = bot_id
        self._bot_secret = bot_secret

    @property
    def is_connected(self) -> bool:
        """获取当前连接状态"""
        if not self._is_connected or self._ws is None:
            return False
        # websockets 12+ 使用 state 属性
        try:
            return self._ws.state.name == "OPEN"
        except:
            return self._is_connected

    async def connect(self) -> None:
        """建立 WebSocket 连接"""
        if self.is_connected:
            self.logger.warn("WebSocket 已连接，跳过重复连接")
            return

        self._is_manual_close = False
        self._reconnect_attempts = 0

        try:
            self.logger.info(f"正在连接 WebSocket: {self.ws_url}")
            self._ws = await websockets.connect(
                self.ws_url,
                ping_interval=None,  # 我们自己管理心跳
                ping_timeout=None,
            )

            self._is_connected = True
            self._missed_pong_count = 0

            if self.on_connected:
                self.on_connected()

            # 启动接收任务
            self._receive_task = asyncio.create_task(self._receive_loop())

            # 发送认证帧
            await self._send_auth()

            # 启动心跳
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            self.logger.info("WebSocket 连接成功")

        except Exception as e:
            self.logger.error(f"WebSocket 连接失败: {e}")
            self._is_connected = False
            if self.on_error:
                self.on_error(e)
            await self._schedule_reconnect()

    async def disconnect(self) -> None:
        """主动断开连接"""
        self._is_manual_close = True
        self._is_connected = False
        self._is_authenticated = False

        # 停止心跳
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

        # 停止接收
        if self._receive_task:
            self._receive_task.cancel()
            self._receive_task = None

        # 清理待处理消息
        self._clear_pending_messages("连接已断开")

        # 关闭 WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None

        self.logger.info("WebSocket 连接已断开")

        if self.on_disconnected:
            self.on_disconnected("手动断开")

    async def _send_auth(self) -> None:
        """发送认证帧"""
        if not self._bot_id or not self._bot_secret:
            self.logger.error("未设置认证凭证")
            return

        req_id = generate_req_id("auth")
        auth_frame = {
            "cmd": WsCmd.SUBSCRIBE,
            "headers": {"req_id": req_id},
            "body": {
                "bot_id": self._bot_id,
                "secret": self._bot_secret,
            },
        }

        self.logger.debug(f"发送认证帧: {req_id}")
        await self._send_raw(auth_frame)

    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while self.is_connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"心跳发送失败: {e}")

    async def _send_heartbeat(self) -> None:
        """发送心跳"""
        if not self.is_connected:
            return

        # 检查连续丢失 pong 次数
        if self._missed_pong_count >= self.MAX_MISSED_PONG:
            self.logger.warn(f"连续 {self._missed_pong_count} 次未收到 pong，触发重连")
            await self._schedule_reconnect()
            return

        req_id = generate_req_id("ping")
        heartbeat_frame = {
            "cmd": WsCmd.HEARTBEAT,
            "headers": {"req_id": req_id},
        }

        self._missed_pong_count += 1
        self.logger.debug(f"发送心跳: {req_id}, 未响应次数: {self._missed_pong_count}")
        await self._send_raw(heartbeat_frame)

    async def _receive_loop(self) -> None:
        """接收消息循环"""
        while self.is_connected and self._ws:
            try:
                message = await self._ws.recv()
                await self._handle_message(message)
            except websockets.ConnectionClosed as e:
                self.logger.warn(f"WebSocket 连接关闭: {e}")
                if not self._is_manual_close:
                    await self._schedule_reconnect()
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"接收消息失败: {e}")
                if self.on_error:
                    self.on_error(e)

    async def _handle_message(self, message: str) -> None:
        """处理收到的消息"""
        try:
            data = json.loads(message)
            frame = WsFrame(
                cmd=data.get("cmd"),
                headers=data.get("headers", {}),
                body=data.get("body"),
                errcode=data.get("errcode"),
                errmsg=data.get("errmsg"),
            )

            # 处理认证/心跳响应
            if frame.errcode is not None:
                if frame.errcode == 0:
                    # 认证成功或心跳响应
                    if not self._is_authenticated:
                        self._is_authenticated = True
                        self._reconnect_attempts = 0
                        self.logger.info("认证成功")
                        if self.on_authenticated:
                            self.on_authenticated()

                    # 心跳响应，重置丢失计数
                    if frame.cmd is None or frame.cmd == WsCmd.HEARTBEAT:
                        self._missed_pong_count = max(0, self._missed_pong_count - 1)

                    # 处理回执
                    req_id = frame.headers.get("req_id", "")
                    if req_id in self._pending_acks:
                        self._handle_reply_ack(req_id, frame)
                else:
                    self.logger.error(f"收到错误响应: errcode={frame.errcode}, errmsg={frame.errmsg}")
                    # 回执错误
                    req_id = frame.headers.get("req_id", "")
                    if req_id in self._pending_acks:
                        self._handle_reply_ack(req_id, frame, error=Exception(frame.errmsg or "未知错误"))
                return

            # 处理消息/事件回调
            if frame.cmd in (WsCmd.CALLBACK, WsCmd.EVENT_CALLBACK):
                if self.on_message:
                    self.on_message(frame)

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析失败: {e}")
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")

    async def _schedule_reconnect(self) -> None:
        """安排重连"""
        if self._is_manual_close:
            return

        self._is_connected = False
        self._is_authenticated = False

        # 检查重连次数限制
        if self.max_reconnect_attempts > 0 and self._reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error(f"已达到最大重连次数 {self.max_reconnect_attempts}，停止重连")
            if self.on_disconnected:
                self.on_disconnected("达到最大重连次数")
            return

        self._reconnect_attempts += 1

        # 计算退避延迟
        delay = min(
            self.reconnect_base_delay * (2 ** (self._reconnect_attempts - 1)),
            self.RECONNECT_MAX_DELAY,
        )

        self.logger.info(f"将在 {delay}ms 后进行第 {self._reconnect_attempts} 次重连")

        if self.on_reconnecting:
            self.on_reconnecting(self._reconnect_attempts)

        await asyncio.sleep(delay / 1000)

        if not self._is_manual_close:
            await self.connect()

    def send(self, frame: WsFrame) -> None:
        """发送数据帧（同步包装）"""
        asyncio.create_task(self._send_raw(frame))

    async def _send_raw(self, data: dict | WsFrame) -> None:
        """发送原始数据"""
        if not self.is_connected or not self._ws:
            self.logger.error("WebSocket 未连接")
            return

        if isinstance(data, WsFrame):
            data = {
                "cmd": data.cmd,
                "headers": data.headers,
                "body": data.body,
            }
            if data.get("cmd") is None:
                del data["cmd"]
            if data.get("body") is None:
                del data["body"]

        try:
            await self._ws.send(json.dumps(data))
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")

    async def send_reply(self, req_id: str, body: Any, cmd: str = WsCmd.RESPONSE) -> WsFrame:
        """
        通过 WebSocket 通道发送回复消息（串行队列版本）

        同一个 req_id 的消息会被放入队列中串行发送：
        发送一条后等待服务端回执，收到回执或超时后才发送下一条。

        Args:
            req_id: 透传回调中的 req_id
            body: 回复消息体
            cmd: 发送的命令类型，默认 aibot_respond_msg

        Returns:
            WsFrame，收到回执时返回回执帧，        """
        loop = asyncio.get_event_loop()
        future: asyncio.Future[WsFrame] = loop.create_future()

        # 检查队列大小
        queue = self._reply_queues.get(req_id, [])
        if len(queue) >= self.MAX_REPLY_QUEUE_SIZE:
            raise Exception(f"回复队列已满，最大长度: {self.MAX_REPLY_QUEUE_SIZE}")

        # 添加到队列
        item = ReplyQueueItem(body=body, cmd=cmd, future=future)
        queue.append(item)
        self._reply_queues[req_id] = queue

        # 如果队列只有一项，立即处理
        if len(queue) == 1:
            await self._process_reply_queue(req_id)

        # 等待 Future 完成
        return await future

    async def _process_reply_queue(self, req_id: str) -> None:
        """处理指定 req_id 的回复队列"""
        queue = self._reply_queues.get(req_id, [])
        if not queue:
            return

        item = queue[0]

        # 构建发送帧
        frame = {
            "cmd": item.cmd,
            "headers": {"req_id": req_id},
            "body": item.body,
        }

        # 发送消息
        await self._send_raw(frame)

        # 设置回执超时
        pending = PendingAck(future=item.future)
        pending.timer = asyncio.create_task(self._ack_timeout(req_id))
        self._pending_acks[req_id] = pending

    async def _ack_timeout(self, req_id: str) -> None:
        """回执超时处理"""
        await asyncio.sleep(self.REPLY_ACK_TIMEOUT / 1000)

        pending = self._pending_acks.pop(req_id, None)
        if pending and not pending.future.done():
            error = Exception(f"回执超时: {req_id}")
            pending.future.set_exception(error)
            self.logger.warn(f"回执超时: {req_id}")

            # 继续处理队列中的下一条
            self._pop_and_continue_queue(req_id)

    def _handle_reply_ack(self, req_id: str, frame: WsFrame, error: Exception | None = None) -> None:
        """处理回复消息的回执"""
        pending = self._pending_acks.pop(req_id, None)
        if not pending:
            return

        # 取消超时定时器
        if pending.timer:
            pending.timer.cancel()

        # 设置结果
        if not pending.future.done():
            if error:
                pending.future.set_exception(error)
            else:
                pending.future.set_result(frame)

        # 继续处理队列中的下一条
        self._pop_and_continue_queue(req_id)

    def _pop_and_continue_queue(self, req_id: str) -> None:
        """弹出队列头部并继续处理"""
        queue = self._reply_queues.get(req_id, [])
        if queue:
            queue.pop(0)

        if queue:
            # 还有消息，继续处理
            asyncio.create_task(self._process_reply_queue(req_id))
        else:
            # 队列为空，删除
            self._reply_queues.pop(req_id, None)

    def _clear_pending_messages(self, reason: str) -> None:
        """清理所有待处理的消息和回执"""
        # 清理队列
        for req_id, queue in self._reply_queues.items():
            for item in queue:
                if not item.future.done():
                    item.future.set_exception(Exception(reason))
        self._reply_queues.clear()

        # 清理待确认
        for req_id, pending in self._pending_acks.items():
            if pending.timer:
                pending.timer.cancel()
            if not pending.future.done():
                pending.future.set_exception(Exception(reason))
        self._pending_acks.clear()
