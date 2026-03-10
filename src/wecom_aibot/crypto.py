"""
加解密工具模块
提供文件加解密相关的功能函数
"""

from __future__ import annotations
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def decrypt_file(encrypted_buffer: bytes, aes_key: str) -> bytes:
    """
    使用 AES-256-CBC 解密文件

    Args:
        encrypted_buffer: 加密的文件数据
        aes_key: Base64 编码的 AES-256 密钥

    Returns:
        解密后的文件 bytes

    Raises:
        ValueError: 密钥格式错误
    """
    # Base64 解码密钥
    try:
        key = base64.b64decode(aes_key)
    except Exception as e:
        raise ValueError(f"无效的 AES 密钥格式: {e}")

    # AES-256 需要 32 字节密钥
    if len(key) != 32:
        raise ValueError(f"AES-256 密钥长度应为 32 字节，实际为 {len(key)} 字节")

    # IV 是密钥的前 16 字节
    iv = key[:16]

    # 创建解密器
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # 解密并去除填充
    decrypted = cipher.decrypt(encrypted_buffer)
    try:
        decrypted = unpad(decrypted, AES.block_size)
    except ValueError:
        # 如果去除填充失败，可能是数据本身没有填充
        pass

    return decrypted
