"""
Unit tests for the Redis configuration settings.

Verifies that the default configurations for Redis host, port, and URL
are correctly defined and loaded.
"""

# Local imports
from src.config.redis import RedisConfig, redis_config


class TestRedisConfig:
    """Test suite for the Redis configuration settings."""

    def test_redis_config_defaults(self) -> None:
        """
        Verify that RedisConfig has the expected default attributes and values.

        Returns
        -------
        None
        """
        assert isinstance(redis_config, RedisConfig)
        assert redis_config.REDIS_HOST == "localhost"
        assert redis_config.REDIS_PORT == 6379
        assert redis_config.REDIS_URL == "redis://localhost:6379/0"
