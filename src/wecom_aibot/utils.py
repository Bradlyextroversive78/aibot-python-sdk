"""通用工具方法"""

from __future__ import annotations
import random
import string
import time


def generate_random_string(length: int = 8) -> str:
    """
    生成随机字符串

    Args:
        length: 随机字符串长度，默认 8

    Returns:
        随机字符串
    """
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def generate_req_id(prefix: str) -> str:
    """
    生成唯一请求 ID

    格式：`{prefix}_{timestamp}_{random}`

    Args:
        prefix: 前缀，通常为 cmd 名称

    Returns:
        唯一请求 ID
    """
    timestamp = int(time.time() * 1000)
    random_str = generate_random_string(8)
    return f"{prefix}_{timestamp}_{random_str}"
