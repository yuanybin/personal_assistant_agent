import time

import pytest
from fastapi.testclient import TestClient

from src.channels.wechat_work.crypto import WeworkCrypto

FAKE_TOKEN = "test_token"
FAKE_AES_KEY = "YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWE"  # base64 of 32 bytes, no pad
FAKE_CORP_ID = "test_corp_id"


@pytest.fixture
def wework_crypto():
    return WeworkCrypto(FAKE_TOKEN, FAKE_AES_KEY, FAKE_CORP_ID)


def test_wework_encrypt_decrypt(wework_crypto: WeworkCrypto):
    """企业微信：加密后再解密应还原明文。"""
    xml = "<xml><ToUserName>corp</ToUserName><Content>hello</Content></xml>"
    encrypted = wework_crypto.encrypt(xml)
    decrypted, corp_id = wework_crypto.decrypt(encrypted)
    assert decrypted == xml
    assert corp_id == FAKE_CORP_ID


def test_wework_signature(wework_crypto: WeworkCrypto):
    """企业微信：正确签名应验证通过。"""
    encrypt = "test_encrypt_msg"
    sig, ts, nonce = _make_signature(wework_crypto, encrypt)
    assert wework_crypto.verify_signature(sig, ts, nonce, encrypt)


def test_wework_bad_signature(wework_crypto: WeworkCrypto):
    """企业微信：错误签名应验证失败。"""
    assert not wework_crypto.verify_signature("bad_sig", "1", "2", "encrypt")


def test_wework_url_verification_flow(client: TestClient, wework_crypto: WeworkCrypto):
    """企业微信 GET URL 验证：应返回解密后的 echostr。"""
    echostr = "test_echo_12345"
    encrypted_echostr = wework_crypto.encrypt(echostr)

    sig, ts, nonce = _make_signature(wework_crypto, encrypted_echostr)

    response = client.get(
        "/api/v1/channels/wechat_work/callback",
        params={
            "msg_signature": sig,
            "timestamp": ts,
            "nonce": nonce,
            "echostr": encrypted_echostr,
        },
    )
    assert response.status_code == 200
    assert response.text == echostr


def test_wework_text_message(client: TestClient, wework_crypto: WeworkCrypto):
    """企业微信文本消息解析。"""
    inner_xml = (
        "<xml>"
        "<ToUserName>corp</ToUserName>"
        "<FromUserName>user001</FromUserName>"
        "<CreateTime>1700000000</CreateTime>"
        "<MsgType>text</MsgType>"
        "<Content>Hello WeChat</Content>"
        "<MsgId>123456</MsgId>"
        "<AgentID>1</AgentID>"
        "</xml>"
    )
    encrypted = wework_crypto.encrypt(inner_xml)

    sig, ts, nonce = _make_signature(wework_crypto, encrypted)

    outer_xml = (
        f"<xml>"
        f"<ToUserName>corp</ToUserName>"
        f"<Encrypt>{encrypted}</Encrypt>"
        f"<AgentID>1</AgentID>"
        f"</xml>"
    )

    response = client.post(
        "/api/v1/channels/wechat_work/callback",
        content=outer_xml,
        params={
            "msg_signature": sig,
            "timestamp": ts,
            "nonce": nonce,
        },
        headers={"Content-Type": "application/xml"},
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0


def test_health_check(client: TestClient):
    """健康检查端点。"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "platforms" in data


def _make_signature(crypto: WeworkCrypto, encrypt: str) -> tuple[str, str, str]:
    ts = str(int(time.time()))
    nonce = "test_nonce"
    sorted_str = "".join(sorted([crypto.token, ts, nonce, encrypt]))
    import hashlib
    sig = hashlib.sha1(sorted_str.encode("utf-8")).hexdigest()
    return sig, ts, nonce
