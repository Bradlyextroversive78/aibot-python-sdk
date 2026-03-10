"""事件相关类型定义"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from enum import StrEnum


class EventType(StrEnum):
    """事件类型枚举"""

    ENTER_CHAT = "enter_chat"
    TEMPLATE_CARD_EVENT = "template_card_event"
    FEEDBACK_EVENT = "feedback_event"


@dataclass
class EventFrom:
    """事件发送者信息（比 MessageFrom 多了 corpid 字段）"""

    userid: str
    corpid: str | None = None


@dataclass
class EnterChatEvent:
    """进入会话事件"""

    eventtype: Literal[EventType.ENTER_CHAT] = EventType.ENTER_CHAT


@dataclass
class TemplateCardEventData:
    """模板卡片事件"""

    eventtype: Literal[EventType.TEMPLATE_CARD_EVENT] = EventType.TEMPLATE_CARD_EVENT
    event_key: str | None = None
    task_id: str | None = None


@dataclass
class FeedbackEventData:
    """用户反馈事件"""

    eventtype: Literal[EventType.FEEDBACK_EVENT] = EventType.FEEDBACK_EVENT


EventContent = EnterChatEvent | TemplateCardEventData | FeedbackEventData


@dataclass
class EventMessage:
    """事件回调消息结构"""

    msgid: str
    create_time: int
    aibotid: str
    from_: EventFrom
    msgtype: Literal["event"]
    event: EventContent
    chatid: str | None = None
    chattype: Literal["single", "group"] | None = None
