from typing import Any, Optional

from pydantic import BaseModel, Field


class DingtalkTextContent(BaseModel):
    content: str = ""


class DingtalkImageContent(BaseModel):
    picURL: str = ""


class DingtalkFileContent(BaseModel):
    downloadCode: str = ""
    fileName: str = ""


class DingtalkWebhookPayload(BaseModel):
    msgtype: str
    text: Optional[DingtalkTextContent] = None
    image: Optional[DingtalkImageContent] = None
    file: Optional[DingtalkFileContent] = None
    voice: Optional[dict[str, Any]] = None
    video: Optional[dict[str, Any]] = None
    link: Optional[dict[str, Any]] = None
    msgId: Optional[str] = None
    createAt: Optional[int] = None
    conversationType: Optional[str] = None
    conversationId: Optional[str] = None
    conversationTitle: Optional[str] = None
    senderId: Optional[str] = None
    senderNick: Optional[str] = None
    senderCorpId: Optional[str] = None
    sessionWebhook: Optional[str] = None
    sessionWebhookExpiredTime: Optional[int] = None
    chatbotCorpId: Optional[str] = None
    chatbotUserId: Optional[str] = None
    atUsers: Optional[list[dict[str, Any]]] = None
