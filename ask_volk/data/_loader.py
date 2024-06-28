from dataclasses import dataclass

import pandas as pd

from ask_volk.config.base import DataConfig


@dataclass
class Loaded:
    """Container for loaded datasets"""

    votes: list[pd.DataFrame]
    text: list[pd.DataFrame]
    controls: list[pd.DataFrame]


class Loader:
    """Helper class to load datasets."""

    def __init__(self, cfg: DataConfig) -> None:
        """Initialize the Loader class."""
        self._cfg = cfg

    def _load_votes(self) -> list[pd.DataFrame]:
        vote_dfs = []
        for vote_dataset in self._cfg.votes_datasets:
            df = pd.read_csv(vote_dataset.path)
            df_subset = pd.DataFrame(
                {
                    "municipality": df[vote_dataset.municipality_column],
                    "canton": df[vote_dataset.canton_column],
                    "vote": df[vote_dataset.vote_column],
                    "yes": df[vote_dataset.yes_column],
                }
            )
            vote_dfs.append(df_subset)
        return vote_dfs

    def _load_text_or_topics(self) -> list[pd.DataFrame]:
        text_dfs = []
        for dataset in self._cfg.topics_dataset:
            df = pd.read_csv(dataset.path)
            if dataset.text_column is not None:
                cols = (
                    dataset.text_column
                    if isinstance(dataset.text_column, list)
                    else df.filter(regex=dataset.text_column).columns
                )
            else:
                cols = (
                    dataset.topic_column
                    if isinstance(dataset.topic_column, list)
                    else df.filter(regex=dataset.topic_column).columns
                )
            df_subset = pd.DataFrame(
                {
                    "vote": df[dataset.vote_column],
                    **{column: df[column] for column in cols},
                }
            )
            text_dfs.append(df_subset)
        return text_dfs

    def _load_controls(self) -> list[pd.DataFrame]:
        controls_dfs = []
        for dataset in self._cfg.controls_dataset:
            df = pd.read_csv(dataset.path)
            cols = (
                dataset.feature_column
                if isinstance(dataset.feature_column, list)
                else df.filter(regex=dataset.feature_column).columns
            )
            if dataset.id_column is not None:
                level: str = dataset.level if dataset.level is not None else "municipality"
                df_subset = pd.DataFrame(
                    {
                        level: df[dataset.id_column],
                        "vote": df[dataset.vote_column],
                        **{column: df[column] for column in cols},
                    }
                )
            else:
                df_subset = pd.DataFrame(
                    {
                        "vote": df[dataset.vote_column],
                        **{column: df[column] for column in cols},
                    }
                )
            controls_dfs.append(df_subset)
        return controls_dfs

    def load(self) -> Loaded:
        """Load the datasets."""
        vote_dfs = self._load_votes()
        text_dfs = self._load_text_or_topics()
        controls_dfs = self._load_controls()
        return Loaded(votes=vote_dfs, text=text_dfs, controls=controls_dfs)
