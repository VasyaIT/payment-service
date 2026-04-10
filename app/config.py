from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://payments:payments@localhost:5432/payments"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    api_key: str = "test-api-key"
    outbox_poll_interval: int = 2

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
