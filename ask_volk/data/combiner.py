from dataclasses import dataclass

import pandas as pd

from ask_volk.data.loader import Loaded


@dataclass
class Combined:
    """Container for combined datasets."""

    df: pd.DataFrame


class Combiner:
    """Helper class to combine datasets."""

    def __init__(self, loaded: Loaded):
        self._loaded = loaded

    def combine(self) -> pd.DataFrame:
        """Combine the loaded datasets."""
        # 1. Combine vote datasets by stacking them
        if len(self._loaded.votes) > 1:
            df = pd.concat(self._loaded.votes, ignore_index=True)
        else:
            df = self._loaded.votes[0]
        # 2. Combine text datasets by joining onto the vote datasets
        for text_df in self._loaded.text:
            df = pd.merge(df, text_df, how="outer", on="vote")
        # 3. Combine control datasets by joining onto the combined vote and text datasets$
        for controls_df in self._loaded.controls:
            if "municipality" in controls_df.columns:
                pd.merge(df, controls_df, how="outer", on="municipality")
            elif "canton" in df.columns:
                pd.merge(df, controls_df, how="outer", on="canton")
            else:
                # Merge federal and vote-related features on the vote identifier
                pd.merge(df, controls_df, how="outer", on="vote")
        return Combined(df=df)