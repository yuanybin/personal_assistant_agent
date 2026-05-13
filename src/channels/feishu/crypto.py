import hashlib
import hmac

from fastapi import HTTPException, Request


async def verify_feishu_signature(request: Request, verification_token: str) -> None:
    """校验飞书请求签名。

    飞书在请求头中附带 X-Lark-Signature，值为 timestamp + nonce + encrypt_key + body 的 HMAC-SHA256。
    如果校验失败，抛出 HTTPException(401)。
    """
    timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
    nonce = request.headers.get("X-Lark-Request-Nonce", "")
    signature = request.headers.get("X-Lark-Signature", "")

    if not timestamp or not nonce or not signature:
        raise HTTPException(status_code=401, detail="缺少签名参数")

    body = await request.body()
    body_str = body.decode("utf-8")

    sign_str = f"{timestamp}{nonce}{verification_token}{body_str}"
    expected = hmac.new(
        verification_token.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="签名校验失败")
