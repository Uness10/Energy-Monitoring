from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Primary ClickHouse node
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 9000
    clickhouse_http_port: int = 8123

    # Replica ClickHouse node (failover)
    clickhouse_replica_host: str = "localhost"
    clickhouse_replica_port: int = 9001
    clickhouse_replica_http_port: int = 8124

    clickhouse_user: str = "mlab"
    clickhouse_password: str = "mlab_secure_2026"
    clickhouse_db: str = "energy_monitoring"

    jwt_secret: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    model_config = {"env_prefix": "", "case_sensitive": False}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
