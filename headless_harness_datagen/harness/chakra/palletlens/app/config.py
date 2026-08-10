"""PalletLens configuration via pydantic-settings + environment variables."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    model_name: str = "mobilenet_v3_small"          # MODEL_NAME; also "resnet18"
    weights_enum: str = "IMAGENET1K_V1"             # WEIGHTS_ENUM — pinned
    max_upload_mb: int = 10                         # MAX_UPLOAD_MB
    store_images: bool = True                       # STORE_IMAGES
    database_url: str = f"sqlite:///{BASE_DIR / 'palletlens.db'}"  # DATABASE_URL
    category_map_path: str = str(BASE_DIR / "category_map.yaml")   # CATEGORY_MAP_PATH
    profiles_path: str = str(BASE_DIR / "profiles.yaml")           # PROFILES_PATH
    api_key: str | None = None                      # API_KEY (optional)
    assets_dir: str = str(BASE_DIR / "assets")
    min_image_dimension: int = 64
    batch_max_files: int = 25
    torch_num_threads: int = 1
    log_level: str = "INFO"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
