import pandas as pd

from typing import Callable


class Deduplicator:
    """Class to deduplicate data after harmonizing municipality names."""

    @staticmethod
    def deduplicate(data: pd.DataFrame, agg: Callable | None = None) -> pd.DataFrame:
        """Deduplicate the DataFrame by aggregation."""
        if not agg:
            return (
                data.groupby(["YEAR", "GEO_ID", "GEO_NAME", "GEO_LV", "VALUE"]).sum().reset_index()
            )
        return (
            data.groupby(["YEAR", "GEO_ID", "GEO_NAME", "GEO_LV", "VALUE"]).agg(agg).reset_index()
        )
