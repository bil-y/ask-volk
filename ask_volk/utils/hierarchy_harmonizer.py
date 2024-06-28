import io

import pandas as pd
import requests

from ask_volk.config.data import GeoLevel


class HierarchyHarmonizer:
    """Adds missing hierarchical information to a dataframe."""

    API_URL: str = "https://www.agvchapp.bfs.admin.ch/de/state/results/xls"

    CANTON_MAPPING = {
        1: "Zürich",
        2: "Bern / Berne",
        3: "Luzern",
        4: "Uri",
        5: "Schwyz",
        6: "Obwalden",
        7: "Nidwalden",
        8: "Glarus",
        9: "Zug",
        10: "Fribourg / Freiburg",
        11: "Solothurn",
        12: "Basel-Stadt",
        13: "Basel-Landschaft",
        14: "Schaffhausen",
        15: "Appenzell Ausserrhoden",
        16: "Appenzell Innerrhoden",
        17: "St. Gallen",
        18: "Graubünden / Grigioni / Grischun",
        19: "Aargau",
        20: "Thurgau",
        21: "Ticino",
        22: "Vaud",
        23: "Valais / Wallis",
        24: "Neuchâtel",
        25: "Genève",
        26: "Jura",
    }

    CANTON_MAPPING_SHORT = {
        1: "ZH",
        2: "BE",
        3: "LU",
        4: "UR",
        5: "SZ",
        6: "OW",
        7: "NW",
        8: "GL",
        9: "ZG",
        10: "FR",
        11: "SO",
        12: "BS",
        13: "BL",
        14: "SH",
        15: "AR",
        16: "AI",
        17: "SG",
        18: "GR",
        19: "AG",
        20: "TG",
        21: "TI",
        22: "VD",
        23: "VS",
        24: "NE",
        25: "GE",
        26: "JU",
    }

    INVERTED_CANTON_MAPPING = {v: k for k, v in CANTON_MAPPING.items()}
    INVERTED_CANTON_MAPPING_SHORT = {v: k for k, v in CANTON_MAPPING_SHORT.items()}

    COL_RENAMES = {
        "BFS Gde-nummer": "MUN_ID",
        "Gemeindename": "MUN_NAME",
        "Bezirks-nummer": "DIS_ID",
        "Bezirksname": "DIS_NAME",
        "Kanton": "CAN_NAME",
    }

    def __init__(self, snapshot_date):
        """Initialize the harmonizer."""
        self.snapshot_date = snapshot_date
        param = {"SnapshotDate": snapshot_date}
        req = requests.post(self.API_URL, data=param)
        self.df = pd.read_excel(io.BytesIO(req.content))
        self.df["CAN_ID"] = self.df["Kanton"].map(self.INVERTED_CANTON_MAPPING_SHORT)

    def _harmonize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Harmonize the DataFrame."""
        match df.loc[0, "GEO_LV"]:
            case GeoLevel.Level.Federal:
                return df

            case GeoLevel.Level.Cantonal:
                joined = self.df.merge(df, left_on="CAN_ID", right_on="GEO_ID", how="outer")
                return joined

            case GeoLevel.Level.District:
                joined = self.df.merge(df, left_on="Bezirks-nummer", right_on="GEO_ID", how="outer")
                return joined

            case GeoLevel.Level.Municipal:
                joined = self.df.merge(df, left_on="BFS Gde-nummer", right_on="GEO_ID", how="right")
                return joined

    def harmonize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Harmonize the DataFrame."""
        harmonized = self._harmonize(df)
        harmonized.rename(columns=self.COL_RENAMES, inplace=True)
        harmonized.drop(
            columns=["GEO_ID", "GEO_NAME", "GEO_LV", "Hist.-Nummer", "Datum der Aufnahme"],
            inplace=True,
            errors="ignore",
        )
        return harmonized
