from typing import Any

import pandas as pd
import rpy2.robjects as robjects
import rpy2.robjects.packages as rpackages


class MunicipalityHarmonizer:
    """Class to harmonize Swiss geo data."""

    def __init__(self, to_year, inventory_path: Any = None):
        """Initialize the harmonizer."""
        self.smmt = rpackages.importr("SMMT")
        self.inventory_path = (
            inventory_path
            if inventory_path is not None
            else self.smmt.download_municipality_inventory()
        )
        self.mutations_obj = self.smmt.import_CH_municipality_inventory(self.inventory_path)
        self.mutations = self.mutations_obj.rx2("mutations")
        self.as_date = robjects.r["as.Date"]
        self.to_year = to_year

    def harmonize(self, from_year: str, df: pd.DataFrame) -> pd.DataFrame:
        """Harmonize the DataFrame."""
        from_date = f"{from_year}-01-01"
        to_date = f"{self.to_year}-12-31"
        old_state = self.as_date(from_date)
        new_state = self.as_date(to_date)
        mapping_obj = self.smmt.map_old_to_new_state(self.mutations, old_state, new_state)
        mapping_table = mapping_obj.rx2("mapped")
        mapping_df = pd.DataFrame(mapping_table).T
        mapping_df.columns = mapping_table.names
        harmonized = df.merge(mapping_df, left_on="GEO_ID", right_on="bfs_nr_old", how="left")
        harmonized["GEO_ID"] = harmonized["bfs_nr_new"]
        harmonized["GEO_NAME"] = harmonized["name_new"]
        harmonized.drop(columns=mapping_df.columns, inplace=True)
        del old_state, new_state, mapping_obj, mapping_table, mapping_df
        return harmonized

    def name_to_id(self, from_year: str, df: pd.DataFrame) -> Any:
        """Convert a municipality name to a BFS ID."""
        from_date = f"{from_year}-01-01"
        to_date = f"{self.to_year}-12-31"
        old_state = self.as_date(from_date)
        new_state = self.as_date(to_date)
        mapping_obj = self.smmt.map_old_to_new_state(self.mutations, old_state, new_state)
        mapping_table = mapping_obj.rx2("mapped")
        mapping_df = pd.DataFrame(mapping_table).T
        mapping_df.columns = mapping_table.names
        harmonized = df.merge(mapping_df, left_on="GEO_NAME", right_on="name_old", how="left")
        harmonized["GEO_ID"] = harmonized["bfs_nr_new"]
        # This leads to duplicates in the harmonized DataFrame.
        # harmonized["GEO_NAME"] = harmonized["name_new"]
        harmonized.drop(columns=mapping_df.columns, inplace=True)
        del old_state, new_state, mapping_obj, mapping_table, mapping_df
        return harmonized
