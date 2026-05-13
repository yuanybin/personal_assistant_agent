import logging

from fastapi import APIRouter, FastAPI

from .channels.dingtalk.adapter import DingTalkAdapter
from .channels.feishu.adapter import FeishuAdapter
from .channels.registry import AdapterRegistry
from .channels.wechat_work.adapter import WeChatWorkAdapter
from .core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
registry = AdapterRegistry()


def _register_adapters() -> None:
    enabled = settings.channels.enabled

    if "wechat_work" in enabled:
        ww = settings.channels.wechat_work
        registry.register(WeChatWorkAdapter(
            token=ww.token.get_secret_value(),
            encoding_aes_key=ww.encoding_aes_key.get_secret_value(),
            corp_id=ww.corp_id,
        ))
        logger.info("企业微信适配器已注册")

    if "feishu" in enabled:
        fs = settings.channels.feishu
        registry.register(FeishuAdapter(
            verification_token=fs.verification_token.get_secret_value(),
        ))
        logger.info("飞书适配器已注册")

    if "dingtalk" in enabled:
        dt = settings.channels.dingtalk
        registry.register(DingTalkAdapter(
            app_secret=dt.app_secret.get_secret_value(),
        ))
        logger.info("钉钉适配器已注册")

    logger.info(f"已注册平台: {registry.list_platforms()}")


_register_adapters()

app = FastAPI(
    title="Personal Assistant Agent",
    description="个人助手 Agent — 多渠道消息接入",
    version="0.1.0",
)

channel_router = APIRouter(prefix="/api/v1/channels", tags=["channels"])
for adapter in registry:
    adapter.register_routes(channel_router)

app.include_router(channel_router)


@app.get("/api/v1/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "platforms": registry.list_platforms(),
    }
