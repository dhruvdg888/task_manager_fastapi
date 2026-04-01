from pathlib import Path
from pydantic_settings import BaseSettings

# settings for env variables
class Settings(BaseSettings):
    database_hostname: str
    database_password: str
    database_name: str
    database_username: str

    model_config = {
        "env_file": Path(__file__).resolve().parent / ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()