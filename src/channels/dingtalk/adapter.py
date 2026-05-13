import logging
from datetime import datetime, timezone

from fastapi import HTTPException, Request

from ..base import BaseIMAdapter
from ..models import ChatType, MessageType, UnifiedMessage
from .crypto import verify_dingtalk_signature
from .schemas import DingtalkWebhookPayload

logger = logging.getLogger(__name__)


class DingTalkAdapter(BaseIMAdapter):
    """钉钉渠道适配器。"""

    def __init__(self, app_secret: str) -> None:
        self._app_secret = app_secret

    @property
    def platform_name(self) -> str:
        return "dingtalk"

    async def verify_webhook(self, request: Request) -> dict:
        # 钉钉的 URL 验证主要依赖 POST 请求的签名校验，GET 请求简单回包
        return {"status": "ok"}

    async def parse_message(self, request: Request) -> UnifiedMessage:
        await verify_dingtalk_signature(request, self._app_secret)

        body = await request.json()
        payload = DingtalkWebhookPayload.model_validate(body)

        msg_type = _map_message_type(payload.msgtype)

        content = _extract_content(payload)

        chat_type = ChatType.PRIVATE
        if payload.conversationType == "2":
            chat_type = ChatType.GROUP

        create_at = payload.createAt or 0
        try:
            ts = datetime.fromtimestamp(create_at / 1000, tz=timezone.utc)
        except (ValueError, OSError):
            ts = datetime.now(tz=timezone.utc)

        return UnifiedMessage(
            platform=self.platform_name,
            message_type=msg_type,
            message_id=payload.msgId or "",
            timestamp=ts,
            sender_id=payload.senderId or "unknown",
            sender_name=payload.senderNick,
            chat_id=payload.conversationId or "",
            chat_type=chat_type,
            content=content,
            raw_payload=body,
        )


def _map_message_type(dd_type: str) -> MessageType:
    mapping = {
        "text": MessageType.TEXT,
        "image": MessageType.IMAGE,
        "voice": MessageType.VOICE,
        "video": MessageType.VIDEO,
        "file": MessageType.FILE,
        "link": MessageType.LINK,
        "event": MessageType.EVENT,
    }
    return mapping.get(dd_type, MessageType.EVENT)


def _extract_content(payload: DingtalkWebhookPayload) -> dict:
    if payload.msgtype == "text" and payload.text:
        return {"text": payload.text.content}
    if payload.msgtype == "image" and payload.image:
        return {"url": payload.image.picURL}
    if payload.msgtype == "file" and payload.file:
        return {"download_code": payload.file.downloadCode, "file_name": payload.file.fileName}
    if payload.msgtype == "voice" and payload.voice:
        return payload.voice
    if payload.msgtype == "video" and payload.video:
        return payload.video
    if payload.msgtype == "link" and payload.link:
        return payload.link
    return {}
