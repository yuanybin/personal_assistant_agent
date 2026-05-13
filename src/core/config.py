from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class WeChatWorkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WEWORK_")

    token: SecretStr = Field(..., description="回调 Token")
    encoding_aes_key: SecretStr = Field(..., description="43 位 AES 密钥")
    corp_id: str = Field(..., description="企业 ID")


class FeishuSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FEISHU_")

    app_id: str = Field(..., description="App ID")
    app_secret: SecretStr = Field(..., description="App Secret")
    verification_token: SecretStr = Field(..., description="Verification Token")
    encrypt_key: Optional[SecretStr] = Field(None, description="事件加密密钥（可选）")


class DingTalkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DINGTALK_")

    client_id: str = Field(..., description="AppKey / ClientId")
    app_secret: SecretStr = Field(..., description="AppSecret / ClientSecret")
    robot_code: Optional[str] = Field(None, description="机器人编码（chatbot 模式）")


class ChannelSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHANNELS_")

    enabled: list[str] = Field(
        default=["wechat_work", "feishu", "dingtalk"],
        description="启用的平台列表，逗号分隔"
    )
    wechat_work: WeChatWorkSettings = Field(default_factory=WeChatWorkSettings)
    feishu: FeishuSettings = Field(default_factory=FeishuSettings)
    dingtalk: DingTalkSettings = Field(default_factory=DingTalkSettings)


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SERVER_")

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    environment: str = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    server: ServerSettings = Field(default_factory=ServerSettings)
    channels: ChannelSettings = Field(default_factory=ChannelSettings)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
