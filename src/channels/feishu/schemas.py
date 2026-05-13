from typing import Any, Optional

from pydantic import BaseModel, Field


class FeishuEventHeader(BaseModel):
    event_id: str
    event_type: str
    tenant_key: str
    app_id: str
    create_time: str = ""


class FeishuEvent(BaseModel):
    schema_: str = Field(alias="schema")
    header: FeishuEventHeader
    event: dict[str, Any] = Field(default_factory=dict)
    challenge: Optional[str] = None
    token: Optional[str] = None
    type: Optional[str] = None
