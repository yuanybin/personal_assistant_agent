from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WeworkXmlPayload(BaseModel):
    """企业微信回调 XML 加密后的格式。"""

    model_config = ConfigDict(populate_by_name=True)

    to_user_name: str = Field(alias="ToUserName")
    encrypt: str = Field(alias="Encrypt")
    agent_id: str = Field(default="", alias="AgentID")


class WeworkDecryptedMessage(BaseModel):
    """解密后的消息内容。"""

    to_user_name: str = Field(alias="ToUserName")
    from_user_name: str = Field(alias="FromUserName")
    create_time: int = Field(alias="CreateTime")
    msg_type: str = Field(alias="MsgType")
    content: str = Field(default="", alias="Content")
    msg_id: str = Field(default="", alias="MsgId")
    agent_id: int = Field(default=0, alias="AgentID")
    pic_url: str = Field(default="", alias="PicUrl")
    media_id: str = Field(default="", alias="MediaId")
    format: str = Field(default="", alias="Format")
    recognition: str = Field(default="", alias="Recognition")
    location_x: str = Field(default="", alias="Location_X")
    location_y: str = Field(default="", alias="Location_Y")
    scale: str = Field(default="", alias="Scale")
    label: str = Field(default="", alias="Label")
    title: str = Field(default="", alias="Title")
    description: str = Field(default="", alias="Description")
    url: str = Field(default="", alias="Url")
    event: str = Field(default="", alias="Event")
    event_key: str = Field(default="", alias="EventKey")
    chat_id: str = Field(default="", alias="ChatId")
    chat_type: str = Field(default="", alias="ChatType")

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True)
