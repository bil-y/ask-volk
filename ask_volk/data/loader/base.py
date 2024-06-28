from abc import ABC, abstractmethod
from ask_volk.utils.filter import Filter

import pandas as pd


class BaseLoader(ABC):
    """Base class for a data loader."""

    def __init__(self, config):
        """Initialize the loader."""
        self.config = config
        self._filters = [Filter(f) for f in config.filters]

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Load the data."""
        pass

    def apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply filters to the DataFrame."""
        for f in self._filters:
            df = f.apply(df)
        return df

    def select_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select columns from the DataFrame."""
        if not self.config.columns:
            return df

        if isinstance(self.config.columns, list):
            cols = {col: col for col in self.config.columns}
        else:
            cols = dict(self.config.columns)

        cols["GEO_ID"] = "GEO_ID"
        cols["GEO_NAME"] = "GEO_NAME"
        cols["GEO_LV"] = "GEO_LV"
        cols["YEAR"] = "YEAR"

        df = df[cols.keys()]
        df = df.rename(columns=cols)
        return df
