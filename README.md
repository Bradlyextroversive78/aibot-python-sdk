# wecom-aibot

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

企业微信智能机器人 Python SDK - WebSocket 长连接通道

将 Node.js SDK [`@wecom/aibot-node-sdk`](https://github.com/WecomTeam/aibot-node-sdk) 完整移植到 Python，提供完整的类型提示和异步支持。

## 功能特性

- ✅ WebSocket 长连接（自动认证）
- ✅ 心跳保持与自动重连（指数退避）
- ✅ 消息类型：text, image, mixed, voice, file
- ✅ 流式回复（支持 Markdown）
- ✅ 模板卡片消息
- ✅ 文件下载与 AES-256-CBC 解密
- ✅ 事件回调：enter_chat, template_card_event, feedback_event
- ✅ 完整类型提示 (Type Hints)
- ✅ 异步支持 (asyncio)

## 安装

```bash
# 使用 pip
pip install wecom-aibot

# 或使用 uv
uv add wecom-aibot
```

## 快速开始

### 1. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件
WECOM_BOT_ID=your-bot-id
WECOM_BOT_SECRET=your-secret
```

### 2. 编写代码

```python
import asyncio
from dotenv import load_dotenv
from wecom_aibot import WSClient, WSClientOptions

load_dotenv()

async def main():
    import os

    # 创建客户端
    options = WSClientOptions(
        bot_id=os.getenv("WECOM_BOT_ID"),
        secret=os.getenv("WECOM_BOT_SECRET"),
    )
    client = WSClient(options)

    # 处理文本消息
    @client.on("message.text")
    async def on_text(frame):
        await client.reply_stream(
            frame,
            "stream_001",
            f"收到: {frame.body.text.content}",
            finish=True,
        )

    # 处理进入会话事件
    @client.on("event.enter_chat")
    async def on_enter(frame):
        from wecom_aibot.types import WelcomeTextReplyBody
        await client.reply_welcome(
            frame,
            WelcomeTextReplyBody.create("您好！有什么可以帮您的？")
        )

    # 连接
    client.connect()

    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await client.disconnect()

asyncio.run(main())
```

## API 文档

### WSClientOptions

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `bot_id` | str | 必填 | 机器人 ID（企业微信后台获取） |
| `secret` | str | 必填 | 机器人 Secret |
| `heartbeat_interval` | int | 30000 | 心跳间隔（毫秒） |
| `max_reconnect_attempts` | int | 10 | 最大重连次数，-1 表示无限 |
| `reconnect_interval` | int | 1000 | 重连基础延迟（毫秒） |
| `request_timeout` | int | 10000 | 请求超时（毫秒） |
| `ws_url` | str | wss://openws.work.weixin.qq.com | WebSocket 地址 |
| `logger` | Logger | None | 自定义日志器 |

### 事件列表

#### 连接事件

| 事件名 | 说明 | 回调参数 |
|--------|------|----------|
| `connected` | 连接建立 | 无 |
| `authenticated` | 认证成功 | 无 |
| `disconnected` | 连接断开 | reason: str |
| `reconnecting` | 正在重连 | attempt: int |
| `error` | 发生错误 | error: Exception |

#### 消息事件

| 事件名 | 说明 | frame.body 类型 |
|--------|------|-----------------|
| `message` | 收到消息（所有类型） | BaseMessage |
| `message.text` | 收到文本消息 | TextMessage |
| `message.image` | 收到图片消息 | ImageMessage |
| `message.mixed` | 收到图文混排消息 | MixedMessage |
| `message.voice` | 收到语音消息 | VoiceMessage |
| `message.file` | 收到文件消息 | FileMessage |

#### 事件回调

| 事件名 | 说明 | frame.body 类型 |
|--------|------|-----------------|
| `event` | 收到事件（所有类型） | EventMessage |
| `event.enter_chat` | 用户进入会话 | EventMessage |
| `event.template_card_event` | 模板卡片事件 | EventMessage |
| `event.feedback_event` | 用户反馈事件 | EventMessage |

### 客户端方法

```python
# 连接/断开
client.connect()                      # 建立连接
await client.disconnect()             # 断开连接

# 流式回复
await client.reply_stream(
    frame,                             # 消息帧
    stream_id,                         # 流式消息 ID
    content,                           # 回复内容（支持 Markdown）
    finish=True                        # 是否结束
)

# 欢迎语回复
await client.reply_welcome(
    frame,
    WelcomeTextReplyBody.create("您好！")
)

# 模板卡片回复
await client.reply_template_card(frame, template_card)

# 流式消息 + 模板卡片组合回复
await client.reply_stream_with_card(
    frame, stream_id, content, finish=True,
    template_card=card
)

# 更新模板卡片
await client.update_template_card(frame, template_card, userids=["user1"])

# 主动发送消息
from wecom_aibot.types import SendMarkdownMsgBody
await client.send_message(
    chatid,
    SendMarkdownMsgBody.create("主动推送的消息")
)

# 下载文件（自动解密）
buffer, filename = await client.download_file(url, aes_key)

# 获取连接状态
client.is_connected  # bool
```

## 项目结构

```
src/wecom_aibot/
├── __init__.py          # 包入口
├── client.py            # WSClient 主客户端
├── ws_manager.py        # WebSocket 连接管理器
├── api_client.py        # HTTP API 客户端
├── message_handler.py   # 消息处理器
├── crypto.py            # AES-256-CBC 解密
├── logger.py            # 日志实现
├── utils.py             # 工具函数
└── types/
    ├── __init__.py
    ├── config.py        # 配置类型
    ├── message.py       # 消息类型
    ├── event.py         # 事件类型
    ├── api.py           # API 类型
    └── template_card.py # 模板卡片类型
```

## 依赖

- Python >= 3.11
- websockets >= 12.0
- httpx >= 0.27.0
- pyee >= 11.0.0
- pycryptodome >= 3.20.0

## 开发

```bash
# 克隆项目
git clone https://github.com/your-username/wecom-aibot.git
cd wecom-aibot

# 安装开发依赖
uv sync --extra dev

# 运行示例
uv run python example_basic.py
```

## 相关链接

- [企业微信智能机器人开发文档](https://developer.work.weixin.qq.com/document/path/94838)
- [Node.js SDK 参考](https://github.com/WecomTeam/aibot-node-sdk)

## License

[MIT](LICENSE)
