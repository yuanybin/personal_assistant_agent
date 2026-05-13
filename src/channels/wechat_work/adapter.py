import logging
from datetime import datetime, timezone

from defusedxml.ElementTree import fromstring
from fastapi import HTTPException, Request
from fastapi.responses import PlainTextResponse, Response

from ..base import BaseIMAdapter
from ..models import ChatType, MessageType, UnifiedMessage
from .crypto import WeworkCrypto, WeworkCryptoError
from .schemas import WeworkDecryptedMessage, WeworkXmlPayload

logger = logging.getLogger(__name__)


class WeChatWorkAdapter(BaseIMAdapter):
    """企业微信渠道适配器。"""

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str) -> None:
        self._crypto = WeworkCrypto(token, encoding_aes_key, corp_id)

    @property
    def platform_name(self) -> str:
        return "wechat_work"

    async def verify_webhook(self, request: Request) -> Response:
        msg_signature = self._get_query_param(request, "msg_signature")
        timestamp = self._get_query_param(request, "timestamp")
        nonce = self._get_query_param(request, "nonce")
        echostr = self._get_query_param(request, "echostr")

        if not self._crypto.verify_signature(msg_signature, timestamp, nonce, echostr):
            raise HTTPException(status_code=401, detail="签名校验失败")

        try:
            decrypted, _ = self._crypto.decrypt(echostr)
            return PlainTextResponse(content=decrypted)
        except WeworkCryptoError as e:
            raise HTTPException(status_code=400, detail=f"解密 echostr 失败: {e}")

    async def parse_message(self, request: Request) -> UnifiedMessage:
        msg_signature = self._get_query_param(request, "msg_signature")
        timestamp = self._get_query_param(request, "timestamp")
        nonce = self._get_query_param(request, "nonce")

        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8")

        try:
            xml_root = fromstring(body_str)
            xml_payload = WeworkXmlPayload(
                to_user_name=xml_root.findtext("ToUserName", ""),
                encrypt=xml_root.findtext("Encrypt", ""),
                agent_id=xml_root.findtext("AgentID", ""),
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"XML 解析失败: {e}")

        if not self._crypto.verify_signature(msg_signature, timestamp, nonce, xml_payload.encrypt):
            raise HTTPException(status_code=401, detail="签名校验失败")

        try:
            decrypted_xml, _ = self._crypto.decrypt(xml_payload.encrypt)
        except WeworkCryptoError as e:
            raise HTTPException(status_code=400, detail=f"解密消息失败: {e}")

        try:
            msg_root = fromstring(decrypted_xml)
            msg = WeworkDecryptedMessage(
                ToUserName=msg_root.findtext("ToUserName", ""),
                FromUserName=msg_root.findtext("FromUserName", ""),
                CreateTime=int(msg_root.findtext("CreateTime", "0")),
                MsgType=msg_root.findtext("MsgType", ""),
                Content=msg_root.findtext("Content", ""),
                MsgId=msg_root.findtext("MsgId", ""),
                AgentID=int(msg_root.findtext("AgentID", "0")),
                PicUrl=msg_root.findtext("PicUrl", ""),
                MediaId=msg_root.findtext("MediaId", ""),
                Format=msg_root.findtext("Format", ""),
                Recognition=msg_root.findtext("Recognition", ""),
                Location_X=msg_root.findtext("Location_X", ""),
                Location_Y=msg_root.findtext("Location_Y", ""),
                Scale=msg_root.findtext("Scale", ""),
                Label=msg_root.findtext("Label", ""),
                Title=msg_root.findtext("Title", ""),
                Description=msg_root.findtext("Description", ""),
                Url=msg_root.findtext("Url", ""),
                Event=msg_root.findtext("Event", ""),
                EventKey=msg_root.findtext("EventKey", ""),
                ChatId=msg_root.findtext("ChatId", ""),
                ChatType=msg_root.findtext("ChatType", ""),
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"解密后 XML 解析失败: {e}")

        return self._to_unified(msg)

    def _to_unified(self, msg: WeworkDecryptedMessage) -> UnifiedMessage:
        msg_type = _map_message_type(msg.msg_type)

        content: dict = {}
        if msg.msg_type == "text":
            content = {"text": msg.content}
        elif msg.msg_type == "image":
            content = {"pic_url": msg.pic_url, "media_id": msg.media_id}
        elif msg.msg_type == "voice":
            content = {"media_id": msg.media_id, "format": msg.format, "recognition": msg.recognition}
        elif msg.msg_type == "video":
            content = {"media_id": msg.media_id, "thumb_media_id": msg.label}
        elif msg.msg_type == "location":
            content = {"location_x": msg.location_x, "location_y": msg.location_y, "scale": msg.scale, "label": msg.label}
        elif msg.msg_type == "link":
            content = {"title": msg.title, "description": msg.description, "url": msg.url}
        elif msg.msg_type == "event":
            content = {"event": msg.event, "event_key": msg.event_key}

        chat_type = ChatType.GROUP if msg.chat_type == "group" else ChatType.PRIVATE
        chat_id = msg.chat_id or msg.from_user_name

        try:
            ts = datetime.fromtimestamp(msg.create_time, tz=timezone.utc)
        except (ValueError, OSError):
            ts = datetime.now(tz=timezone.utc)

        return UnifiedMessage(
            platform=self.platform_name,
            message_type=msg_type,
            message_id=msg.msg_id,
            timestamp=ts,
            sender_id=msg.from_user_name,
            chat_id=chat_id,
            chat_type=chat_type,
            content=content,
            raw_payload=msg.to_dict(),
        )

    @staticmethod
    def _get_query_param(request: Request, name: str) -> str:
        value = request.query_params.get(name, "")
        if not value:
            raise HTTPException(status_code=400, detail=f"缺少参数: {name}")
        return value


def _map_message_type(wework_type: str) -> MessageType:
    mapping = {
        "text": MessageType.TEXT,
        "image": MessageType.IMAGE,
        "voice": MessageType.VOICE,
        "video": MessageType.VIDEO,
        "file": MessageType.FILE,
        "location": MessageType.LOCATION,
        "link": MessageType.LINK,
        "event": MessageType.EVENT,
    }
    return mapping.get(wework_type, MessageType.EVENT)
