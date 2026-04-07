from pydantic import Field
from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    api_key: str = Field(default="my-expenses-secret-key", alias="API_KEY")

    # LLM Configuration (for AI expense parsing)
    llm_api_base_url: str = Field(default="http://localhost:8080", alias="LLM_API_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="coder-model", alias="LLM_MODEL")

    class Config:
        env_file = ".env.bot"
        env_file_encoding = "utf-8"
        populate_by_name = True


settings = BotSettings()
