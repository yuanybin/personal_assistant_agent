from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    LOCATION = "location"
    LINK = "link"
    EVENT = "event"


class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"


class UnifiedMessage(BaseModel):
    """各 IM 平台消息归一化后的统一格式。"""

    platform: str = Field(..., description="平台标识：wechat_work / feishu / dingtalk")
    message_type: MessageType = Field(..., description="消息类型")
    message_id: str = Field(..., description="平台唯一消息 ID")
    timestamp: datetime = Field(..., description="消息发送时间（UTC）")
    sender_id: str = Field(..., description="发送者 ID")
    sender_name: Optional[str] = Field(None, description="发送者显示名称")
    chat_id: str = Field(..., description="会话 / 群组 ID")
    chat_type: ChatType = Field(..., description="私聊或群聊")
    content: dict[str, Any] = Field(default_factory=dict, description="归一化内容字段")
    raw_payload: dict[str, Any] = Field(default_factory=dict, exclude=True, description="原始消息（仅供调试）")
