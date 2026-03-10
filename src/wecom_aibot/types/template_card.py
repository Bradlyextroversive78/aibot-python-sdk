"""模板卡片相关类型定义"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from enum import StrEnum


class TemplateCardType(StrEnum):
    """卡片类型枚举"""

    TEXT_NOTICE = "text_notice"
    NEWS_NOTICE = "news_notice"
    BUTTON_INTERACTION = "button_interaction"
    VOTE_INTERACTION = "vote_interaction"
    MULTIPLE_INTERACTION = "multiple_interaction"


@dataclass
class TemplateCardSource:
    """卡片来源样式信息"""

    icon_url: str | None = None
    desc: str | None = None
    desc_color: Literal[0, 1, 2, 3] | None = None


@dataclass
class TemplateCardActionMenu:
    """卡片右上角更多操作按钮"""

    desc: str
    action_list: list[dict[str, str]] = field(default_factory=list)


@dataclass
class TemplateCardMainTitle:
    """模板卡片主标题"""

    title: str | None = None
    desc: str | None = None


@dataclass
class TemplateCardEmphasisContent:
    """关键数据样式"""

    title: str | None = None
    desc: str | None = None


@dataclass
class TemplateCardQuoteArea:
    """引用文献样式"""

    type: Literal[0, 1, 2] | None = None
    url: str | None = None
    appid: str | None = None
    pagepath: str | None = None
    title: str | None = None
    quote_text: str | None = None


@dataclass
class TemplateCardHorizontalContent:
    """二级标题+文本列表"""

    keyname: str
    type: Literal[0, 1, 3] | None = None
    value: str | None = None
    url: str | None = None
    userid: str | None = None


@dataclass
class TemplateCardJumpAction:
    """跳转指引样式"""

    title: str
    type: Literal[0, 1, 2, 3] | None = None
    url: str | None = None
    appid: str | None = None
    pagepath: str | None = None
    question: str | None = None


@dataclass
class TemplateCardAction:
    """整体卡片的点击跳转事件"""

    type: Literal[0, 1, 2]
    url: str | None = None
    appid: str | None = None
    pagepath: str | None = None


@dataclass
class TemplateCardVerticalContent:
    """卡片二级垂直内容"""

    title: str
    desc: str | None = None


@dataclass
class TemplateCardImage:
    """图片样式"""

    url: str
    aspect_ratio: float | None = None


@dataclass
class TemplateCardImageTextArea:
    """左图右文样式"""

    image_url: str
    type: Literal[0, 1, 2] | None = None
    url: str | None = None
    appid: str | None = None
    pagepath: str | None = None
    title: str | None = None
    desc: str | None = None


@dataclass
class TemplateCardSubmitButton:
    """提交按钮样式"""

    text: str
    key: str


@dataclass
class TemplateCardSelectionItem:
    """下拉式选择器"""

    question_key: str
    option_list: list[dict[str, str]] = field(default_factory=list)
    title: str | None = None
    disable: bool | None = None
    selected_id: str | None = None


@dataclass
class TemplateCardButton:
    """模板卡片按钮"""

    text: str
    key: str
    style: int | None = None


@dataclass
class TemplateCardCheckbox:
    """选择题样式（投票选择）"""

    question_key: str
    option_list: list[dict[str, str | bool]] = field(default_factory=list)
    disable: bool | None = None
    mode: Literal[0, 1] | None = None


@dataclass
class TemplateCard:
    """模板卡片结构（通用类型，包含所有可能的字段）"""

    card_type: str
    source: TemplateCardSource | None = None
    action_menu: TemplateCardActionMenu | None = None
    main_title: TemplateCardMainTitle | None = None
    emphasis_content: TemplateCardEmphasisContent | None = None
    quote_area: TemplateCardQuoteArea | None = None
    sub_title_text: str | None = None
    horizontal_content_list: list[TemplateCardHorizontalContent] | None = None
    jump_list: list[TemplateCardJumpAction] | None = None
    card_action: TemplateCardAction | None = None
    card_image: TemplateCardImage | None = None
    image_text_area: TemplateCardImageTextArea | None = None
    vertical_content_list: list[TemplateCardVerticalContent] | None = None
    button_selection: TemplateCardSelectionItem | None = None
    button_list: list[TemplateCardButton] | None = None
    checkbox: TemplateCardCheckbox | None = None
    select_list: list[TemplateCardSelectionItem] | None = None
    submit_button: TemplateCardSubmitButton | None = None
    task_id: str | None = None
    feedback: dict[str, str] | None = None
