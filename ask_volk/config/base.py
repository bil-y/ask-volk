from dataclasses import dataclass
from typing import Optional

from hydra.core.config_store import ConfigStore
from omegaconf import MISSING

from ask_volk.config.data import SocioEconConfig, VotesConfig
from ask_volk.config.model import ModelConfig


@dataclass
class DataConfig:
    """Data configuration class."""

    votes: VotesConfig = MISSING
    socioeconomic: SocioEconConfig = MISSING
    topics: str = MISSING


@dataclass
class HarmonizationConfig:
    """Harmonization configuration class."""

    to_year: int = MISSING
    inventory_path: str = MISSING
    snapshot_date: str = MISSING


@dataclass
class Config:
    """Top-level configuration class."""

    data: DataConfig = MISSING
    model: ModelConfig = MISSING
    harmonization: HarmonizationConfig = MISSING
    data_dir: Optional[str] = None
    model_dir: Optional[str] = None
    debug: bool = False


def register_config():
    """Register the configuration classes."""
    cs = ConfigStore.instance()
    cs.store(name="base_config", node=Config)
    cs.store(group="data", name="base_data", node=DataConfig)
    cs.store(group="data/votes", name="base_votes", node=VotesConfig)
    cs.store(group="data/socioeconomic", name="base_socioeconomic", node=SocioEconConfig)
