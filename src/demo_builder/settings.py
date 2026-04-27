from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    aicore_db_url: str = ""

    # Where rendered demo directories land. Mounted into the Nginx container.
    output_root: str = "/srv/data/demos"

    # Public base URL for the rendered demos (used in copy + share links).
    public_base_url: str = "https://demos.the2357.com"

    # Sentry
    sentry_dsn: str = ""


settings = Settings()
