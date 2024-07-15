from dataclasses import dataclass

from omegaconf import MISSING


@dataclass
class ModelConfig:
    test_cutoff: int = MISSING
