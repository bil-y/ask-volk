import math

import pandas as pd
from pyaxis import pyaxis

from ask_volk.config.data import GeoLevel, SocioEconDataset
from ask_volk.data.loader.base import BaseLoader
from ask_volk.utils.hierarchy_harmonizer import HierarchyHarmonizer
from ask_volk.utils.municipality_harmonizer import MunicipalityHarmonizer
from ask_volk.utils.deduplicator import Deduplicator


class StatTabLoader(BaseLoader):
    """Class to load data from a BFS StatTab files."""

    FORMAT_COL_MAP = {
        GeoLevel.ColFormat.NestedCantonDistrictMunicipalityWithNumber: "Kanton (-) / Bezirk (>>) / Gemeinde (......)",
        GeoLevel.ColFormat.NestedCantonDistrictMunicipality: "Kanton (-) / Bezirk (>>) / Gemeinde (......)",
        GeoLevel.ColFormat.NestedRegionDistrictMunicipality: "Grossregion (<<) / Kanton (-) / Gemeinde (......)",
        GeoLevel.ColFormat.NestedDistrictMunicipality: "Bezirk (>>) / Gemeinde (......)",
        GeoLevel.ColFormat.Canton: "Kanton",
        GeoLevel.ColFormat.MunicipalityWithNumber: "Gemeinde",
        GeoLevel.ColFormat.Municipality: "Gemeinde",
        GeoLevel.ColFormat.Federal: None,
    }

    FORMAT_PATTERN_MAP = {
        GeoLevel.ColFormat.NestedCantonDistrictMunicipalityWithNumber: r"(\d{4})\s*(.*)",
        GeoLevel.ColFormat.NestedCantonDistrictMunicipality: None,
        GeoLevel.ColFormat.NestedRegionDistrictMunicipality: r"(\d{4})\s*(.*)",
        GeoLevel.ColFormat.NestedDistrictMunicipality: None,
        GeoLevel.ColFormat.Canton: r"(\d{2})\s*(.*)",
        GeoLevel.ColFormat.MunicipalityWithNumber: r"(\d{1,4})\s*(.*)",
        GeoLevel.ColFormat.Municipality: r"(\d{4})\s*(.*)",
        GeoLevel.ColFormat.Federal: None,
    }

    def __init__(self, config: SocioEconDataset, harmonizer: MunicipalityHarmonizer) -> None:
        """Initialize the loader."""
        assert config.format == "stattab", "Invalid configuration format"
        super().__init__(config)
        self.config = config
        self.harmonizer = harmonizer
        self._harmonized = False

    def _harmonize_geo_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Harmonize the geo column."""
        match self.config.geolevel.column:
            case (
                GeoLevel.ColFormat.NestedCantonDistrictMunicipalityWithNumber
                | GeoLevel.ColFormat.NestedRegionDistrictMunicipality
            ):
                df = self._filter_geo_level(df)
                df = self._transform_metadata_columns(df)
            case (
                GeoLevel.ColFormat.NestedDistrictMunicipality
                | GeoLevel.ColFormat.NestedCantonDistrictMunicipality
            ):
                df = self._filter_geo_level(df)
                df = self._transform_metadata_columns(df)
                df = self.harmonizer.name_to_id(df["YEAR"].max(), df)
                df.drop(df[df["GEO_NAME"].apply(type) != str].index, inplace=True)
                self._harmonized = True
            case GeoLevel.ColFormat.Municipality:
                df = self._transform_metadata_columns(df)
                df = self.harmonizer.name_to_id(df["YEAR"].max(), df)
                df.drop(df[df["GEO_NAME"].apply(type) != str].index, inplace=True)
                self._harmonized = True
            case GeoLevel.ColFormat.MunicipalityWithNumber | GeoLevel.ColFormat.Canton:
                df = self._transform_metadata_columns(df)
            case GeoLevel.ColFormat.Federal:
                df = self._transform_metadata_columns(df)
                df["GEO_NAME"] = "Schweiz"
                df["GEO_ID"] = 0
                self._harmonized = True
                return df
        return df

    def _filter_geo_level(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter the DataFrame based on the geo level."""
        col = self.FORMAT_COL_MAP[self.config.geolevel.column]
        match self.config.geolevel.level:
            case GeoLevel.Level.Cantonal:
                return df[df[col].str.startswith("-")]
            case GeoLevel.Level.District:
                return df[df[col].str.startswith(">")]
            case GeoLevel.Level.Municipal:
                return df[df[col].str.startswith("......")]

    def _transform_metadata_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the metadata columns (GEO_ID, GEO_NAME, GEO_LV, YEAR)."""
        lv = self.config.geolevel.level
        col_fmt = self.config.geolevel.column
        col = self.FORMAT_COL_MAP[col_fmt]
        pattern = self.FORMAT_PATTERN_MAP[col_fmt]
        match lv, col_fmt:
            case (
                GeoLevel.Level.Municipal,
                GeoLevel.ColFormat.Municipality
                | GeoLevel.ColFormat.NestedCantonDistrictMunicipality
                | GeoLevel.ColFormat.NestedDistrictMunicipality,
            ):
                df["GEO_NAME"] = df[col].str.replace("......", "").str.strip()
            case (
                GeoLevel.Level.Municipal,
                GeoLevel.ColFormat.NestedCantonDistrictMunicipalityWithNumber
                | GeoLevel.ColFormat.NestedRegionDistrictMunicipality
                | GeoLevel.ColFormat.MunicipalityWithNumber,
            ):
                df[["GEO_ID", "GEO_NAME"]] = df[col].str.extract(pattern)
                df.drop(df[df["GEO_ID"].astype(float).apply(math.isnan)].index, inplace=True)
                df["GEO_ID"] = df["GEO_ID"].astype(int)
            case (GeoLevel.Level.Cantonal, _):
                df["GEO_NAME"] = df[col].str.replace(">", "").str.strip()
                df["GEO_ID"] = (
                    df["GEO_NAME"].map(HierarchyHarmonizer.INVERTED_CANTON_MAPPING).astype(int)
                )
        df["GEO_LV"] = lv
        if "Periode" in df.columns:
            df["YEAR"] = df["Periode"].apply(lambda x: x.split("/")[0]).astype(int)
            df.drop(columns=["Periode"], inplace=True)
        else:
            df.rename(columns={"Jahr": "YEAR"}, inplace=True)
        return df

    def load(self) -> pd.DataFrame:
        """Load the data."""
        px = pyaxis.parse(self.config.source, encoding="ISO-8859-1")
        df = px["DATA"]
        df = self.apply_filters(df)
        df = self._harmonize_geo_columns(df)
        df = df.pivot(
            index=self.config.pivot["index"],
            columns=self.config.pivot["columns"],
            values=self.config.pivot["values"],
        ).reset_index()
        df = self.select_columns(df)
        df.columns = ["_".join(filter(None, a)) for a in df.columns.to_flat_index()]
        df = df.melt(
            id_vars=["YEAR", "GEO_ID", "GEO_NAME", "GEO_LV"], var_name="VALUE", value_name="DATA"
        )
        if not self._harmonized:
            df = self.harmonizer.harmonize(df["YEAR"].max(), df)
        df["is_float"] = df["DATA"].str.match(r"^-?\d+(\.\d+)?$")
        df.loc[~df["is_float"], "DATA"] = pd.NA
        df.drop(columns=["is_float"], inplace=True)
        df["DATA"] = df["DATA"].astype("Float32")
        df = Deduplicator.deduplicate(df)
        return df
