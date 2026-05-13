import base64
import hashlib
import logging
import random
import struct
from typing import Optional

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

logger = logging.getLogger(__name__)


class WeworkCryptoError(Exception):
    """企业微信加解密异常。"""


class WeworkCrypto:
    """企业微信消息加解密工具。

    参考：https://developer.work.weixin.qq.com/document/path/90968
    """

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str) -> None:
        self.token = token
        self.corp_id = corp_id
        self.aes_key = base64.b64decode(encoding_aes_key + "=")

        if len(self.aes_key) != 32:
            raise WeworkCryptoError(f"AES 密钥长度应为 32 字节，实际为 {len(self.aes_key)}")

    def verify_signature(self, signature: str, timestamp: str, nonce: str, encrypt: str) -> bool:
        """校验 msg_signature。"""
        expected = self._calc_signature(timestamp, nonce, encrypt)
        return signature == expected

    def decrypt(self, encrypt: str) -> tuple[str, Optional[str]]:
        """解密消息，返回 (明文消息, receive_id)。

        解密后格式：random(16) + msg_len(4) + msg + receive_id
        """
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(self.aes_key[:16]))
        decryptor = cipher.decryptor()
        plain = decryptor.update(base64.b64decode(encrypt)) + decryptor.finalize()

        # 移除 PKCS7 填充
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plain = unpadder.update(plain) + unpadder.finalize()

        # 解析：random(16) + msg_len(4) + msg + receive_id
        msg_len_bytes = plain[16:20]
        msg_len = struct.unpack("!I", msg_len_bytes)[0]

        msg = plain[20:20 + msg_len].decode("utf-8")
        receive_id = plain[20 + msg_len:].decode("utf-8") if len(plain) > 20 + msg_len else None

        return msg, receive_id

    def encrypt(self, msg: str) -> str:
        """加密回复消息。"""
        random_bytes = bytes(random.getrandbits(8) for _ in range(16))
        msg_bytes = msg.encode("utf-8")
        msg_len = struct.pack("!I", len(msg_bytes))
        corp_id_bytes = self.corp_id.encode("utf-8")

        plain = random_bytes + msg_len + msg_bytes + corp_id_bytes

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        plain = padder.update(plain) + padder.finalize()

        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(self.aes_key[:16]))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plain) + encryptor.finalize()

        return base64.b64encode(ciphertext).decode("utf-8")

    def _calc_signature(self, timestamp: str, nonce: str, encrypt: str) -> str:
        sorted_str = "".join(sorted([self.token, timestamp, nonce, encrypt]))
        return hashlib.sha1(sorted_str.encode("utf-8")).hexdigest()
