from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LastApiConfig(BaseModel):
    """Persist last used API host/port for CLI defaults."""

    host: Optional[str] = None
    port: Optional[int] = None


class LastDispatchConfig(BaseModel):
    """Persist last dispatch target (user reply routing)."""

    channel: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class HeartbeatConfig(BaseModel):
    """Heartbeat scheduling configuration."""

    # Keep it permissive: utils only needs the model to exist.
    enabled: bool = True
    interval_minutes: int = Field(default=30, ge=1)
    query_file: str = Field(default="HEARTBEAT.md")


class AgentsDefaultsConfig(BaseModel):
    heartbeat: Optional[HeartbeatConfig] = None


class AgentsConfig(BaseModel):
    """Agent-related configuration loaded from WORKING_DIR/config.json."""

    defaults: AgentsDefaultsConfig = Field(default_factory=AgentsDefaultsConfig)
    system_prompt_files: Optional[list[str]] = None


class Config(BaseModel):
    """Root config model persisted as WORKING_DIR/config.json."""

    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    last_api: LastApiConfig = Field(default_factory=LastApiConfig)
    last_dispatch: Optional[LastDispatchConfig] = None