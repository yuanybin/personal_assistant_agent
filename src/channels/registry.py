from typing import Iterator

from .base import BaseIMAdapter


class AdapterRegistry:
    """IM 适配器注册表，按 platform_name 索引。"""

    def __init__(self) -> None:
        self._adapters: dict[str, BaseIMAdapter] = {}

    def register(self, adapter: BaseIMAdapter) -> None:
        name = adapter.platform_name
        if name in self._adapters:
            raise ValueError(f"适配器 {name!r} 已注册")
        self._adapters[name] = adapter

    def get(self, platform_name: str) -> BaseIMAdapter:
        try:
            return self._adapters[platform_name]
        except KeyError:
            raise ValueError(f"未注册的平台: {platform_name!r}")

    def list_platforms(self) -> list[str]:
        return sorted(self._adapters.keys())

    def __iter__(self) -> Iterator[BaseIMAdapter]:
        return iter(self._adapters.values())
