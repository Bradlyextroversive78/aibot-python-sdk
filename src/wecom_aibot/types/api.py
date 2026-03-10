"""API 相关类型定义"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Any, Callable, Union, TypeAlias
from enum import StrEnum

from wecom_aibot.types.message import BaseMessage, TextMessage, ImageMessage, MixedMessage, VoiceMessage, FileMessage
from wecom_aibot.types.event import EventMessage, EnterChatEvent, TemplateCardEventData, FeedbackEventData
from wecom_aibot.types.template_card import TemplateCard


class WsCmd(StrEnum):
    """WebSocket 命令类型常量"""

    SUBSCRIBE = "aibot_subscribe"
    HEARTBEAT = "ping"
    RESPONSE = "aibot_respond_msg"
    RESPONSE_WELCOME = "aibot_respond_welcome_msg"
    RESPONSE_UPDATE = "aibot_respond_update_msg"
    SEND_MSG = "aibot_send_msg"
    CALLBACK = "aibot_msg_callback"
    EVENT_CALLBACK = "aibot_event_callback"


@dataclass
class WsFrame:
    """
    WebSocket 帧结构

    发送和接收统一使用 { cmd, headers, body } 格式：
    - 认证发送：{ cmd: "aibot_subscribe", headers: { req_id }, body: { secret, bot_id } }
    - 消息推送：{ cmd: "aibot_msg_callback", headers: { req_id }, body: { msgid, msgtype, ... } }
    - 事件推送：{ cmd: "aibot_event_callback", headers: { req_id }, body: { event_type, ... } }
    - 回复消息：{ cmd: "aibot_respond_msg", headers: { req_id }, body: { msgtype, stream: { ... } } }
    - 回复欢迎语：{ cmd: "aibot_respond_welcome_msg", headers: { req_id }, body: { ... } }
    - 更新模板卡片：{ cmd: "aibot_respond_update_msg", headers: { req_id }, body: { ... } }
    - 心跳发送：{ cmd: "ping", headers: { req_id } }
    - 认证/心跳响应：{ headers: { req_id }, errcode: 0, errmsg: "ok" }
    """

    headers: dict[str, Any]
    cmd: str | None = None
    body: Any = None
    errcode: int | None = None
    errmsg: str | None = None


WsFrameHeaders = WsFrame  # 简化类型，仅包含 headers 的帧


@dataclass
class ReplyFeedback:
    """回复消息中的反馈信息"""

    id: str


@dataclass
class ReplyMsgItem:
    """回复消息中的图文混排子项"""

    msgtype: Literal["image"]
    image: dict[str, str]  # { base64: str, md5: str }


@dataclass
class StreamReplyBody:
    """流式回复消息体"""

    msgtype: Literal["stream"] = "stream"
    stream: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        stream_id: str,
        content: str | None = None,
        finish: bool = False,
        msg_item: list[ReplyMsgItem] | None = None,
        feedback: ReplyFeedback | None = None,
    ) -> "StreamReplyBody":
        """创建流式回复消息体"""
        stream: dict[str, Any] = {"id": stream_id}
        if content is not None:
            stream["content"] = content
        if finish:
            stream["finish"] = True
        if msg_item:
            stream["msg_item"] = [{"msgtype": item.msgtype, "image": item.image} for item in msg_item]
        if feedback:
            stream["feedback"] = {"id": feedback.id}
        return cls(stream=stream)


@dataclass
class WelcomeTextReplyBody:
    """欢迎语回复消息体（文本类型）"""

    msgtype: Literal["text"] = "text"
    text: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(cls, content: str) -> "WelcomeTextReplyBody":
        return cls(text={"content": content})


@dataclass
class WelcomeTemplateCardReplyBody:
    """欢迎语回复消息体（模板卡片类型）"""

    msgtype: Literal["template_card"] = "template_card"
    template_card: TemplateCard = field(default_factory=TemplateCard)


@dataclass
class SendMarkdownMsgBody:
    """主动发送 Markdown 消息体"""

    msgtype: Literal["markdown"] = "markdown"
    markdown: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(cls, content: str) -> "SendMarkdownMsgBody":
        return cls(markdown={"content": content})


@dataclass
class SendTemplateCardMsgBody:
    """主动发送模板卡片消息体"""

    msgtype: Literal["template_card"] = "template_card"
    template_card: TemplateCard = field(default_factory=TemplateCard)


# 事件回调类型
MessageCallback: TypeAlias = Callable[[WsFrame], None]
EventCallback: TypeAlias = Callable[[WsFrame], None]
VoidCallback: TypeAlias = Callable[[], None]
ErrorCallback: TypeAlias = Callable[[Exception], None]
ReconnectingCallback: TypeAlias = Callable[[int], None]
DisconnectedCallback: TypeAlias = Callable[[str], None]


@dataclass
class WSClientEventMap:
    """WSClient 事件映射类型（用于类型提示）"""

    # 消息事件
    message: MessageCallback | None = None
    message_text: MessageCallback | None = None
    message_image: MessageCallback | None = None
    message_mixed: MessageCallback | None = None
    message_voice: MessageCallback | None = None
    message_file: MessageCallback | None = None
    # 事件回调
    event: EventCallback | None = None
    event_enter_chat: EventCallback | None = None
    event_template_card_event: EventCallback | None = None
    event_feedback_event: EventCallback | None = None
    # 连接事件
    connected: VoidCallback | None = None
    authenticated: VoidCallback | None = None
    disconnected: DisconnectedCallback | None = None
    reconnecting: ReconnectingCallback | None = None
    error: ErrorCallback | None = None
