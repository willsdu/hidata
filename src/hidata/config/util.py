from typing import Optional

from pathlib import Path
from .config import Config
from ..constant import WORKING_DIR
import json

def get_config_path() -> Path:
    return WORKING_DIR.joinpath("config.json")

def load_config(configPath: Optional[Path]=None) -> Config:
    if configPath is None:
        configPath = get_config_path()

    if not configPath.is_file():
        return Config()
    with open(configPath, "r",encoding="utf-8") as file:
        data=json.load(file)
    return Config.model_validate(data)