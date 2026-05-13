import base64
import hashlib
import hmac
import time

from fastapi.testclient import TestClient


FAKE_SECRET = "test_dingtalk_secret"


def make_dingtalk_signature(timestamp: str, secret: str = FAKE_SECRET) -> str:
    sign_str = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(hmac_code).decode("utf-8")


def test_dingtalk_url_verification(client: TestClient):
    """钉钉 GET 回调：应简单返回 ok。"""
    response = client.get("/api/v1/channels/dingtalk/callback")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dingtalk_text_message(client: TestClient):
    """钉钉文本消息解析。"""
    timestamp = str(int(time.time() * 1000))
    sign = make_dingtalk_signature(timestamp)

    body = {
        "msgtype": "text",
        "text": {"content": "Hello DingTalk"},
        "msgId": "msg_001",
        "createAt": int(time.time() * 1000),
        "conversationType": "1",
        "conversationId": "conv_001",
        "senderId": "user_001",
        "senderNick": "Test User",
    }

    response = client.post(
        "/api/v1/channels/dingtalk/callback",
        json=body,
        headers={"timestamp": timestamp, "sign": sign},
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0


def test_dingtalk_bad_signature(client: TestClient):
    """钉钉：错误签名应返回 401。"""
    response = client.post(
        "/api/v1/channels/dingtalk/callback",
        json={"msgtype": "text", "text": {"content": "test"}},
        headers={"timestamp": "12345", "sign": "bad_signature"},
    )
    assert response.status_code == 401
