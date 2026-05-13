# personal_assistant_agent

个人助手 Agent — 多渠道 IM 消息接入网关，统一对接企业微信、飞书、钉钉的 Webhook 回调，将各平台消息归一化为统一格式。

## 架构

```
                    ┌─────────────────────┐
                    │   FastAPI Server     │
                    │   /api/v1/channels/  │
                    └──────┬──────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    企业微信 Webhook   飞书 Webhook   钉钉 Webhook
    /wechat_work/     /feishu/       /dingtalk/
    callback           callback       callback
           │               │               │
    ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
    │ WeworkAdapter│ │FeishuAdapter│ │DingTalkAdapter│
    └──────┴──────┘ └──────┴──────┘ └──────┴──────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                    ┌──────┴──────┐
                    │UnifiedMessage│
                    └─────────────┘
```

- **适配器模式**：`BaseIMAdapter` 抽象基类定义两个核心接口：
  - `verify_webhook` — 处理 GET 请求（URL 验证/echostr/challenge）
  - `parse_message` — 处理 POST 请求（签名校验、解密、解析 → `UnifiedMessage`）
- **统一消息模型**：`UnifiedMessage` 将各平台消息归一化，包含消息类型、发送者、会话、内容等字段
- **配置驱动**：通过 `.env` 环境变量按需启用平台，无需改代码

## 快速开始

```bash
# 1. 安装依赖
pip install -e ".[dev]"

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入各平台的 Token/AppSecret 等凭据

# 3. 启动服务
uvicorn src.main:app --reload --port 8000
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `CHANNELS_ENABLED` | 启用的平台列表，逗号分隔：`wechat_work,feishu,dingtalk` |
| `SERVER_HOST` | 监听地址，默认 `0.0.0.0` |
| `SERVER_PORT` | 监听端口，默认 `8000` |
| `WEWORK_TOKEN` | 企业微信回调 Token |
| `WEWORK_ENCODING_AES_KEY` | 企业微信 43 位 AES 密钥 |
| `WEWORK_CORP_ID` | 企业微信企业 ID |
| `FEISHU_APP_ID` / `FEISHU_APP_SECRET` / `FEISHU_VERIFICATION_TOKEN` | 飞书应用凭据 |
| `DINGTALK_CLIENT_ID` / `DINGTALK_APP_SECRET` | 钉钉应用凭据 |
| `DINGTALK_ROBOT_CODE` | 钉钉机器人编码（chatbot 模式，可选） |

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/health` | 健康检查，返回启用的平台列表 |
| `GET` | `/api/v1/channels/{platform}/callback` | 平台 URL 验证 |
| `POST` | `/api/v1/channels/{platform}/callback` | 接收平台消息回调 |

其中 `{platform}` 为 `wechat_work`、`feishu`、`dingtalk`。

## 项目结构

```
src/
├── main.py                  # 应用入口，注册路由
├── core/
│   └── config.py            # pydantic-settings 配置模型
├── channels/
│   ├── base.py              # BaseIMAdapter 抽象基类
│   ├── registry.py          # AdapterRegistry 注册表
│   ├── models.py            # UnifiedMessage 统一消息模型
│   ├── wechat_work/         # 企业微信适配器 + 加解密 + Schema
│   ├── feishu/              # 飞书适配器 + 签名校验 + Schema
│   └── dingtalk/            # 钉钉适配器 + 签名校验 + Schema
├── pipeline/                # 消息处理管线（预留）
└── langchain_usage/         # LangChain/LangGraph Agent 示例
```

## 技术栈

- **Web 框架**：FastAPI + Uvicorn
- **数据模型**：Pydantic v2 + pydantic-settings
- **HTTP 客户端**：httpx
- **加密**：cryptography、pycryptodome
- **XML 解析**：defusedxml（防 XML 注入）
- **LangChain 生态**：langchain、langgraph（Agent 开发）
- **测试**：pytest + pytest-asyncio
- **代码质量**：ruff、mypy

## 开发

```bash
# 运行测试
pytest

# 代码检查
ruff check src/ tests/
mypy src/
```

## License

MIT
