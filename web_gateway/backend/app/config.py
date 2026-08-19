from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'ROS2 Web Gateway v0.1'
    cors_origins: str = 'http://localhost:3000'
    recordings_dir: Path = Path('/recordings')
    ros_domain_id: int = 0

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @property
    def origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',')]


settings = Settings()
