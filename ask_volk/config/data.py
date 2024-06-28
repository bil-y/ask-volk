import operator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from omegaconf import MISSING


@dataclass
class Filter:
    """Filter for a DataFrame."""

    key: str = MISSING
    op: Any = MISSING
    value: Any = MISSING

    def __post_init__(self) -> None:
        """Post-initialization method."""
        self.op = Filter.str_to_op(self.op)

    @staticmethod
    def str_to_op(op: str) -> Callable[[Any, Any], bool]:
        """Convert a string to a function."""
        return {
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            "<": operator.lt,
            ">=": operator.ge,
            "<=": operator.le,
            "in": lambda x, y: x.apply(lambda z: any([i == z for i in y])),
            "not in": lambda x, y: x.apply(lambda z: not any([i == z for i in y])),
        }[op]  # type: ignore

    def as_tuple(self) -> tuple[str, Callable[[Any, Any], bool], Any]:
        """Return the filter as a tuple."""
        return self.key, self.op, self.value


@dataclass
class Pivot:
    """Pivot configuration for a DataFrame."""

    index: list[str] = MISSING
    columns: list[str] = MISSING
    values: list[str] = MISSING


@dataclass
class GeoLevel:
    """GeoLevel configuration for a DataFrame."""

    class Level(Enum):
        """GeoLevel levels."""

        Federal = "federal"
        Cantonal = "cantonal"
        District = "district"
        Municipal = "municipality"

    class ColFormat(Enum):
        """GeoLevel column formats."""

        NestedCantonDistrictMunicipalityWithNumber = (
            "nested_canton_district_municipality_with_number"
        )
        NestedCantonDistrictMunicipality = "nested_canton_district_municipality"
        NestedRegionDistrictMunicipality = "nested_region_district_municipality"
        NestedDistrictMunicipality = "nested_dis_mun"
        Canton = "canton"
        Municipality = "municipality"
        MunicipalityWithNumber = "municipality_with_number"
        Federal = "federal"

    level: Level = Level.Municipal
    column: ColFormat = ColFormat.NestedCantonDistrictMunicipalityWithNumber
    filter: bool = True


@dataclass
class VoteDataset:
    """Configuration for a votes DataFrame."""

    geolevel: GeoLevel = MISSING
    votedates: Optional[list[str]] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    lang: str = "de"
    cache_dir: Optional[str] = None


@dataclass
class VotesConfig:
    """Configuration for a votes DataFrame."""

    cantonal: Optional[VoteDataset] = None
    national: Optional[VoteDataset] = None
    swissvotes: Optional[VoteDataset] = None


@dataclass
class SocioEconDataset:
    """Configuration for a socio-economic DataFrame."""

    format: str = MISSING
    source: Any = MISSING
    filters: Optional[list[Filter]] = field(default_factory=list)  # type: ignore
    columns: Optional[dict[str, str]] = field(default_factory=dict)  # type: ignore
    pivot: Optional[Pivot] = None
    geolevel: GeoLevel = field(default_factory=lambda: GeoLevel(level=GeoLevel.Level.Municipal))

    def __post__init__(self) -> None:
        """Post-initialization method."""
        if not isinstance(self.source, (str, dict)):
            raise ValueError("Source must be a string or a dictionary")
        if isinstance(self.source, str) and format == "statlas":
            raise ValueError("Statlas source must dictionary year -> source")
        if isinstance(self.source, dict) and format == "stattab":
            raise ValueError("Stattab source must be a string")


@dataclass
class SocioEconConfig:
    """Configuration for a socio-economic DataFrame."""

    data: list[SocioEconDataset] = MISSING
    cache_dir: Optional[str] = None
