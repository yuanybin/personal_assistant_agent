# CLAUDE.md

本文件为 Claude Code（claude.ai/code）在本仓库中工作时提供指导。

## 项目概述

个人助手 Agent — 旨在提升工作效率、处理个人事务。当前实现了多渠道 IM 消息接入网关，统一对接企业微信、飞书、钉钉的 Webhook 回调，将各平台消息归一化为 `UnifiedMessage`。

## 开发环境

- **Python 版本**：>=3.9,<3.13
- **IDE**：PyCharm（`.idea/` 已提交）
- **包管理**：pip + `pyproject.toml`（无 poetry/uv）

## 构建 / 测试 / 代码检查

```bash
pip install -e ".[dev]"        # 安装依赖
pytest                          # 运行测试（pytest + pytest-asyncio）
ruff check src/ tests/          # 代码检查
mypy src/                       # 类型检查
```

## 架构

### 适配器模式（channels/）

```
BaseIMAdapter (抽象基类)
├── WeChatWorkAdapter   → /api/v1/channels/wechat_work/callback
├── FeishuAdapter       → /api/v1/channels/feishu/callback
└── DingTalkAdapter     → /api/v1/channels/dingtalk/callback
```

每个适配器实现两个核心方法：
- `verify_webhook()` — GET 请求：URL 验证（echostr / challenge）
- `parse_message()` — POST 请求：签名校验 → 解密 → 解析为 `UnifiedMessage`

### 关键模块

| 模块 | 职责 |
|------|------|
| `src/main.py` | FastAPI 应用入口，按配置注册平台路由 |
| `src/core/config.py` | pydantic-settings 分层配置（Server/Channel/各平台） |
| `src/channels/base.py` | `BaseIMAdapter` 抽象基类 + `register_routes()` |
| `src/channels/registry.py` | 适配器注册表，按 `platform_name` 索引 |
| `src/channels/models.py` | `UnifiedMessage` 统一消息模型 |
| `src/channels/{platform}/crypto.py` | 平台特有的签名校验 / 加解密 |
| `src/channels/{platform}/schemas.py` | 平台特有的 Pydantic 请求/消息模型 |
| `src/channels/{platform}/adapter.py` | 平台适配器实现 |
| `src/langchain_usage/` | LangChain/LangGraph Agent 示例代码 |
| `src/pipeline/` | 消息处理管线（预留，待实现） |

### 配置

- `.env` 驱动，通过 `pydantic-settings` 自动加载
- 各平台凭据使用 `SecretStr`，序列化时自动遮蔽
- `CHANNELS_ENABLED` 按需启用平台，无需改代码
