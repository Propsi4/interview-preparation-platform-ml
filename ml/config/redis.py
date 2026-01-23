"""
Redis configuration settings.

Provides configuration for Redis using the redis driver.
Environment variables use the prefix REDIS_ (e.g., REDIS_HOST, REDIS_PORT).
"""

# Thirdparty imports
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv(override=True)


class RedisConfig(BaseSettings):
    """
    Connection configuration for the Redis of the interview preparation platform.

    Parameters
    ----------
    REDIS_HOST: str
        Redis host
    REDIS_PORT: int
        Redis port

    Examples
    --------
    >>> cfg = RedisConfig()
    >>> print(cfg.REDIS_HOST)
    localhost
    """

    REDIS_HOST: str = Field(
        default="localhost",
        description="Redis host",
    )
    REDIS_PORT: int = Field(
        default=6379,
        description="Redis port",
    )

    @property
    def REDIS_URL(self) -> str:
        """Constructs the Redis connection URL from individual components."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


redis_config = RedisConfig()
