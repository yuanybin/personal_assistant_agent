from abc import ABC, abstractmethod

from fastapi import APIRouter, Request

from .models import UnifiedMessage


class BaseIMAdapter(ABC):
    """IM 渠道适配器抽象基类。

    每个平台适配器负责：
    1. Webhook URL 验证（GET 请求）
    2. 消息解析与归一化（POST 请求）
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台唯一标识：wechat_work / feishu / dingtalk。"""
        ...

    @abstractmethod
    async def verify_webhook(self, request: Request) -> dict:
        """处理 URL 验证（echostr / challenge）。

        验证失败抛出 HTTPException(401)。
        """
        ...

    @abstractmethod
    async def parse_message(self, request: Request) -> UnifiedMessage:
        """解析 webhook POST 请求体为 UnifiedMessage。

        步骤：
        1. 校验签名 / 解密请求体
        2. 解析平台格式 → 平台模型
        3. 转换为 UnifiedMessage

        解析失败抛出 HTTPException(400/401)。
        """
        ...

    @property
    def route_prefix(self) -> str:
        return f"/{self.platform_name}"

    def register_routes(self, router: APIRouter) -> None:
        """在 router 上注册 GET 和 POST 回调端点。"""

        @router.get(f"{self.route_prefix}/callback")
        async def get_callback(request: Request):
            return await self.verify_webhook(request)

        @router.post(f"{self.route_prefix}/callback")
        async def post_callback(request: Request):
            message = await self.parse_message(request)
            return {"code": 0, "msg": "ok"}
