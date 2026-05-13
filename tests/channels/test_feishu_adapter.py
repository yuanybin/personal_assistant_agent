import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient


FAKE_TOKEN = "test_verification_token"


def _sign(timestamp: str, nonce: str, body: str, token: str = FAKE_TOKEN) -> str:
    sign_str = f"{timestamp}{nonce}{token}{body}"
    return hmac.new(
        token.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def test_feishu_url_verification(client: TestClient):
    body = {
        "schema": "2.0",
        "header": {"event_id": "1", "event_type": "", "tenant_key": "t", "app_id": "a"},
        "type": "url_verification",
        "token": FAKE_TOKEN,
        "challenge": "test_challenge_123",
    }
    response = client.request(
        "GET",
        "/api/v1/channels/feishu/callback",
        content=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json() == {"challenge": "test_challenge_123"}


def test_feishu_url_verification_bad_token(client: TestClient):
    body = {
        "schema": "2.0",
        "header": {"event_id": "1", "event_type": "", "tenant_key": "t", "app_id": "a"},
        "type": "url_verification",
        "token": "wrong_token",
        "challenge": "test_challenge_123",
    }
    response = client.request(
        "GET",
        "/api/v1/channels/feishu/callback",
        content=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_feishu_text_message(client: TestClient):
    body = {
        "schema": "2.0",
        "header": {
            "event_id": "evt_001",
            "event_type": "im.message.receive_v1",
            "tenant_key": "tenant_1",
            "app_id": "app_1",
            "create_time": str(int(time.time() * 1000)),
        },
        "event": {
            "sender": {
                "sender_id": {"open_id": "user_001"},
                "sender_name": "Test User",
            },
            "message": {
                "message_id": "msg_001",
                "chat_id": "chat_001",
                "chat_type": "p2p",
                "message_type": "text",
                "content": json.dumps({"text": "Hello"}),
            },
        },
    }
    body_str = json.dumps(body)
    timestamp = str(int(time.time()))
    nonce = "test_nonce"
    signature = _sign(timestamp, nonce, body_str)

    response = client.post(
        "/api/v1/channels/feishu/callback",
        content=body_str,
        headers={
            "Content-Type": "application/json",
            "X-Lark-Request-Timestamp": timestamp,
            "X-Lark-Request-Nonce": nonce,
            "X-Lark-Signature": signature,
        },
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0


def test_feishu_bad_signature(client: TestClient):
    body_str = json.dumps({
        "schema": "2.0",
        "header": {"event_id": "1", "event_type": "", "tenant_key": "t", "app_id": "a"},
        "event": {},
    })
    response = client.post(
        "/api/v1/channels/feishu/callback",
        content=body_str,
        headers={
            "Content-Type": "application/json",
            "X-Lark-Request-Timestamp": "123",
            "X-Lark-Request-Nonce": "abc",
            "X-Lark-Signature": "bad_signature",
        },
    )
    assert response.status_code == 401
