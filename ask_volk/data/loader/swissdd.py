import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import rpy2.robjects as robjects
import rpy2.robjects.packages as rpackages

from ask_volk.config.data import VotesConfig


def get_swissvotes(cache_dir: str | None = None):
    """
    Load the Swiss votes dataset from the swissdd package.
    """
    swissdd = rpackages.importr("swissdd")
    writecsv = robjects.r["write.csv"]
    sv = swissdd.get_swissvotes()
    if cache_dir is not None:
        with open(Path(cache_dir) / "swiss_votes.csv", "w") as f:
            writecsv(sv, f.name)
            swiss_votes = pd.read_csv(f.name)
    else:
        with tempfile.NamedTemporaryFile(suffix=".csv") as f:
            writecsv(sv, f.name)
            swiss_votes = pd.read_csv(f.name)
    return swiss_votes


def get_nationalvotes(
    geolevel: str = "municipality",
    votedates: list[str] | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    lang: str = "DE",
    cache_dir: str | None = None,
):
    """
    Load the Swiss national votes dataset from the swissdd package.
    """
    swissdd = rpackages.importr("swissdd")
    writecsv = robjects.r["write.csv"]

    cache_file = (
        (
            Path(cache_dir)
            / f"national_votes_{geolevel}_{votedates}_{from_date}_{to_date}_{lang}.csv"
        )
        if cache_dir is not None
        else None
    )

    if cache_file is not None and cache_file.exists():
        return pd.read_csv(cache_file)

    nv = swissdd.get_nationalvotes(
        geolevel=geolevel,
        votedates=votedates if votedates is not None else robjects.NULL,
        from_date=from_date if from_date is not None else robjects.NULL,
        to_date=to_date if to_date is not None else robjects.NULL,
        language=lang,
    )
    if cache_file is not None:
        with open(cache_file, "w") as f:
            writecsv(nv, f.name)
            national_votes = pd.read_csv(f.name)
    else:
        with tempfile.NamedTemporaryFile(suffix=".csv") as f:
            writecsv(nv, f.name)
            national_votes = pd.read_csv(f.name)
    return national_votes


def get_cantonalvotes(
    geolevel: str = "municipality",
    votedates: list[str] | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    cache_dir: str | None = None,
):
    """
    Load the Swiss cantonal votes dataset from the swissdd package.
    """
    swissdd = rpackages.importr("swissdd")
    writecsv = robjects.r["write.csv"]

    cache_file = (
        (Path(cache_dir) / f"cantonal_votes_{geolevel}_{votedates}_{from_date}_{to_date}.csv")
        if cache_dir is not None
        else None
    )

    if cache_file is not None and cache_file.exists():
        return pd.read_csv(cache_file)

    cv = swissdd.get_cantonalvotes(
        geolevel=geolevel, votedates=votedates, from_date=from_date, to_date=to_date
    )
    if cache_file is not None:
        with open(cache_file, "w") as f:
            writecsv(cv, f.name)
            national_votes = pd.read_csv(f.name)
    else:
        with tempfile.NamedTemporaryFile(suffix=".csv") as f:
            writecsv(cv, f.name)
            national_votes = pd.read_csv(f.name)
    return national_votes


@dataclass
class VotesData:
    """Data class to hold vote data."""

    national: pd.DataFrame | None = None
    cantonal: pd.DataFrame | None = None
    swissvotes: pd.DataFrame | None = None


class VotesLoader:
    """Class to load vote data from the swissdd package."""

    def __init__(self, config: VotesConfig) -> None:
        """Initialize the loader."""
        self.config = config

    def load(self) -> pd.DataFrame:
        """Load the vote data."""
        votes = VotesData()
        if self.config.national is not None:
            votes.national = get_nationalvotes(
                geolevel=self.config.national.geolevel.level.value,
                votedates=self.config.national.votedates,
                from_date=self.config.national.from_date,
                to_date=self.config.national.to_date,
                lang=self.config.national.lang,
                cache_dir=self.config.national.cache_dir,
            )
        if self.config.cantonal is not None:
            votes.cantonal = get_cantonalvotes(
                geolevel=self.config.cantonal.geolevel.level.value,
                votedates=self.config.cantonal.votedates,
                from_date=self.config.cantonal.from_date,
                to_date=self.config.cantonal.to_date,
                cache_dir=self.config.cantonal.cache_dir,
            )

        if self.config.swissvotes is not None:
            votes.swissvotes = get_swissvotes(cache_dir=self.config.swissvotes.cache_dir)
        return votes
