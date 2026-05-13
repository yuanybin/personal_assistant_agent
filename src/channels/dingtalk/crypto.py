import hashlib
import hmac

from fastapi import HTTPException, Request


async def verify_dingtalk_signature(request: Request, app_secret: str) -> None:
    """校验钉钉请求签名。

    钉钉签名算法：HmacSHA256(timestamp + "\n" + app_secret)，结果 Base64 编码。
    签名放在请求头 X-Sign 或 query param sign 中。
    校验失败抛出 HTTPException(401)。
    """
    timestamp = request.headers.get("timestamp", "")
    sign = request.headers.get("sign", "")

    if not timestamp or not sign:
        raise HTTPException(status_code=401, detail="缺少签名参数")

    sign_str = f"{timestamp}\n{app_secret}"
    hmac_code = hmac.new(
        app_secret.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    expected = _base64_encode(hmac_code)

    if not hmac.compare_digest(expected, sign):
        raise HTTPException(status_code=401, detail="签名校验失败")


def _base64_encode(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode("utf-8")
