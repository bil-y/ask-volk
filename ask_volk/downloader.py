from pathlib import Path

import hydra
from alive_progress import alive_bar

from ask_volk.config.base import Config, register_config
from ask_volk.data.loader.statlas import StatlasLoader
from ask_volk.data.loader.stattab import StatTabLoader
from ask_volk.data.loader.swissdd import VotesLoader
from ask_volk.utils.hierarchy_harmonizer import HierarchyHarmonizer
from ask_volk.utils.municipality_harmonizer import MunicipalityHarmonizer

register_config()


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: Config) -> None:
    if not cfg.data_dir:
        data_dir = (
            Path(hydra.core.hydra_config.HydraConfig.get().runtime.output_dir) / "intermediate"
        )
    else:
        data_dir = Path(cfg.data_dir) / "intermediate"

    # 0. Initialize the GeoHarmonizer
    mun_harmonizer = MunicipalityHarmonizer(
        to_year=cfg.harmonization.to_year, inventory_path=cfg.harmonization.inventory_path
    )
    hier_harmonizer = HierarchyHarmonizer(snapshot_date=cfg.harmonization.snapshot_date)

    # 1. Load votes data
    votes_data = VotesLoader(cfg.data.votes).load()

    if votes_data.national is not None:
        votes_data.national.to_csv(data_dir / "national_votes.csv", index=False)
    if votes_data.cantonal is not None:
        votes_data.cantonal.to_csv(data_dir / "cantonal_votes.csv", index=False)
    if votes_data.swissvotes is not None:
        votes_data.swissvotes.to_csv(data_dir / "swissvotes.csv", index=False)

    controls_dir = data_dir / "controls"

    # 2. Load socio-economic data
    with alive_bar(len(cfg.data.socioeconomic.data)) as bar:
        for i, dataset_cfg in enumerate(cfg.data.socioeconomic.data):
            df = (
                StatlasLoader(dataset_cfg, mun_harmonizer).load()
                if dataset_cfg.format == "statlas"
                else StatTabLoader(dataset_cfg, mun_harmonizer).load()
            )
            df = hier_harmonizer.harmonize(df)
            df.to_parquet(controls_dir / f"socioeconomic_{i}.parquet", index=False)
            bar()


if __name__ == "__main__":
    main()
