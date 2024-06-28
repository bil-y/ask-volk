from dataclasses import dataclass

from omegaconf import MISSING

@dataclass
class VoteModelConfig:
    """Configuration for the vote model.

    Attributes:
        model: str: Name of the model to use.
        params: dict: Parameters to pass to the model.
    """

    model: str = MISSING
    params: dict = MISSING


@dataclass
class TextModelConfig:
    """Configuration for the text model.

    Attributes:
        model: str: Name of the model to use.
        params: dict: Parameters to pass to the model.
    """

    model: str = MISSING
    params: dict = MISSING
