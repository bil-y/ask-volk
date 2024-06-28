from ask_volk.config.data import SocioEconDataset
from ask_volk.data.loader.base import BaseLoader
from ask_volk.utils.municipality_harmonizer import MunicipalityHarmonizer

from pathlib import Path

import pandas as pd


class StatlasLoader(BaseLoader):
    """Class to load data from the Statlas"""

    def __init__(self, config: SocioEconDataset, harmonizer: MunicipalityHarmonizer) -> None:
        """Initialize the loader."""
        super().__init__(config)
        assert config.format == "statlas", "Invalid configuration format"
        self.config = config
        self.harmonizer = harmonizer

    def load(self) -> pd.DataFrame:
        """Load the data."""
        dfs = {
            year: self.harmonizer.harmonize(from_year=year, df=pd.read_csv(url, sep=";"))
            for year, url in self.config.source.items()
        }
        for year, df in dfs.items():
            if isinstance(year, str) and "-" in year:
                start, end = map(int, year.split("-"))
                for i in range(start, end + 1):
                    dfs[i] = df
                del dfs[year]

        df = pd.concat(dfs, names=["YEAR"]).reset_index().drop(columns=["level_1"])
        df["GEO_LV"] = self.config.geolevel.level
        df = self.apply_filters(df)
        df = self.select_columns(df)

        return df
