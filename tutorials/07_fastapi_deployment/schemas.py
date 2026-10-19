from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120, description="任务标题")
    description: str | None = Field(default=None, max_length=1000, description="任务描述")


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=4000, description="用户输入")


class ChatResponse(BaseModel):
    reply: str
    mode: Literal["demo", "deepseek"]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
