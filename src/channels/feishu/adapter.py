import json
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, Request

from ..base import BaseIMAdapter
from ..models import ChatType, MessageType, UnifiedMessage
from .crypto import verify_feishu_signature
from .schemas import FeishuEvent

logger = logging.getLogger(__name__)


class FeishuAdapter(BaseIMAdapter):
    """飞书（Lark）渠道适配器。"""

    def __init__(self, verification_token: str) -> None:
        self._verification_token = verification_token

    @property
    def platform_name(self) -> str:
        return "feishu"

    async def verify_webhook(self, request: Request) -> dict:
        body = await request.json()
        event = FeishuEvent.model_validate(body)

        if event.type == "url_verification":
            token = event.token or ""
            challenge = event.challenge or ""
            if token != self._verification_token:
                raise HTTPException(status_code=401, detail="Token 不匹配")
            return {"challenge": challenge}

        raise HTTPException(status_code=400, detail="未知的验证请求类型")

    async def parse_message(self, request: Request) -> UnifiedMessage:
        await verify_feishu_signature(request, self._verification_token)

        body = await request.json()
        event = FeishuEvent.model_validate(body)

        header = event.header
        payload = event.event

        message_data = payload.get("message", {})
        sender_data = payload.get("sender", {})
        sender_id_data = sender_data.get("sender_id", {})

        sender_id = sender_id_data.get("open_id", sender_id_data.get("user_id", "unknown"))
        chat_id = message_data.get("chat_id", "")
        msg_type_str = message_data.get("message_type", "text")
        message_id = message_data.get("message_id", "")

        msg_type = _map_message_type(msg_type_str)
        content_str = message_data.get("content", "{}")
        try:
            content = json.loads(content_str) if isinstance(content_str, str) else content_str
        except json.JSONDecodeError:
            content = {"text": content_str}

        chat_type_str = message_data.get("chat_type", "p2p")
        chat_type = ChatType.GROUP if chat_type_str == "group" else ChatType.PRIVATE

        create_time_str = header.create_time
        try:
            ts = datetime.fromtimestamp(int(create_time_str) / 1000, tz=timezone.utc)
        except (ValueError, TypeError):
            ts = datetime.now(tz=timezone.utc)

        return UnifiedMessage(
            platform=self.platform_name,
            message_type=msg_type,
            message_id=message_id,
            timestamp=ts,
            sender_id=sender_id,
            sender_name=sender_data.get("sender_name"),
            chat_id=chat_id,
            chat_type=chat_type,
            content=content,
            raw_payload=body,
        )


def _map_message_type(feishu_type: str) -> MessageType:
    mapping = {
        "text": MessageType.TEXT,
        "image": MessageType.IMAGE,
        "audio": MessageType.VOICE,
        "media": MessageType.FILE,
        "file": MessageType.FILE,
        "sticker": MessageType.IMAGE,
        "post": MessageType.TEXT,
        "share_chat": MessageType.EVENT,
    }
    return mapping.get(feishu_type, MessageType.EVENT)
