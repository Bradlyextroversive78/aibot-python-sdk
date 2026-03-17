"""
测试上传并发送文件

使用方法：
1. 确保 .env 文件中配置了 WECOM_BOT_ID 和 WECOM_BOT_SECRET
2. 运行: uv run python test_upload_file.py
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    from wecom_aibot import WSClient
    from wecom_aibot.types import WSClientOptions, UploadMediaOptions
    from wecom_aibot.exceptions import UploadError

    bot_id = os.getenv("WECOM_BOT_ID")
    secret = os.getenv("WECOM_BOT_SECRET")
    target_userid = os.getenv("WECOM_TARGET_USERID")

    if not bot_id or not secret:
        print("[ERROR] 请在 .env 文件中设置 WECOM_BOT_ID 和 WECOM_BOT_SECRET")
        return

    print(f"[CONFIG] Bot ID: {bot_id}")
    print(f"[CONFIG] Target User: {target_userid or '未配置'}")

    # 读取测试文件
    file_path = "testfile.xlsx"
    print(f"[FILE] 读取文件: {file_path}")

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        print(f"[FILE] 文件大小: {len(file_bytes)} 字节 ({len(file_bytes) / 1024:.2f} KB)")
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {file_path}")
        return

    # 创建客户端
    options = WSClientOptions(bot_id=bot_id, secret=secret)
    client = WSClient(options)

    upload_result = None

    @client.on("connected")
    def on_connected():
        print("[WS] 已连接")

    @client.on("authenticated")
    async def on_authenticated():
        nonlocal upload_result
        print("[WS] 认证成功")
        print("[UPLOAD] 开始上传文件...")

        try:
            upload_result = await client.uploadMedia(
                file_bytes,
                UploadMediaOptions(type="file", filename="testfile.xlsx"),
            )
            print(f"[UPLOAD] OK - 上传成功!")
            print(f"         media_id: {upload_result.media_id}")
            print(f"         type: {upload_result.type}")
            print(f"         created_at: {upload_result.created_at}")

            # 如果配置了目标用户，主动发送
            if target_userid:
                print(f"[SEND] 发送文件给用户: {target_userid}")
                await client.sendMediaMessage(target_userid, "file", upload_result.media_id)
                print(f"[SEND] OK - 文件已发送!")
            else:
                print("[INFO] 未配置 WECOM_TARGET_USERID，跳过主动发送")
                print("[INFO] 发送任意文本消息给机器人，它将回复此文件")

        except UploadError as e:
            print(f"[ERROR] 上传失败: {e}")
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")

    @client.on("message.text")
    async def on_text_message(frame):
        nonlocal upload_result
        print(f"[MSG] 收到文本: {frame.body.text.content}")

        if not upload_result:
            print("[UPLOAD] 先上传文件...")
            upload_result = await client.uploadMedia(
                file_bytes,
                UploadMediaOptions(type="file", filename="testfile.xlsx"),
            )
            print(f"[UPLOAD] OK - media_id: {upload_result.media_id}")

        print("[REPLY] 回复文件...")
        await client.replyMedia(frame, "file", upload_result.media_id)
        print("[REPLY] OK - 文件已回复!")

    @client.on("error")
    def on_error(error):
        print(f"[ERROR] {error}")

    @client.on("disconnected")
    def on_disconnected(reason):
        print(f"[WS] 断开连接: {reason}")

    # 连接
    print("[START] 正在连接...")
    client.connect()

    # 保持运行
    print("[INFO] 等待操作... (Ctrl+C 退出)")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n[STOP] 正在断开...")
        await client.disconnect()
        print("[BYE] 已断开连接")


if __name__ == "__main__":
    asyncio.run(main())
