from pydantic import Field, BaseModel



class AgentConfig(BaseModel):
    language: str=Field(default="zh-CN",description="Language for MD files")


class Config(BaseModel):
    agent: AgentConfig=Field(default_factory=AgentConfig)