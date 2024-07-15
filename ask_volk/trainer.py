import pickle
from pathlib import Path

import hydra
import pandas as pd
import shap
import xgboost as xgb

from ask_volk.config.base import Config, register_config
from ask_volk.config.data import VotesConfig

register_config()


def _load_votes(cfg: VotesConfig, data_dir: Path) -> pd.DataFrame:
    cantonal = None
    national = None
    swissvotes = None
    if cfg.cantonal is not None:
        cantonal = pd.read_csv(data_dir / "cantonal_votes.csv")
    if cfg.national is not None:
        national = pd.read_csv(data_dir / "national_votes.csv")
    if cfg.swissvotes is not None:
        swissvotes = pd.read_csv(data_dir / "swissvotes.csv")
    return {"cantonal": cantonal, "national": national, "swissvotes": swissvotes}


def _load_topics(topics_file: Path | str) -> pd.DataFrame:
    topics = pd.read_csv(topics_file)
    return topics


def _preprocess_votes(votes_data: dict, topics: pd.DataFrame) -> pd.DataFrame:
    # Currently only using national votes
    nv = votes_data["national"]
    nv["id"] /= 10
    nv = nv[nv["id"] >= topics["id"].min()]
    nv.dropna(inplace=True)
    nv_and_topics = nv.merge(topics, left_on="id", right_on="id")
    nv_and_topics["votedate"] = pd.DatetimeIndex(nv_and_topics["votedate"])
    nv_and_topics["year"] = nv_and_topics["votedate"].dt.year
    nv_and_topics["month"] = nv_and_topics["votedate"].dt.month / 12
    return nv_and_topics


def _preprocess_dataset(controls: pd.DataFrame, votes_and_topics: pd.DataFrame) -> pd.DataFrame:
    controls = controls.pivot(index=["YEAR", "MUN_ID"], columns="VALUE", values="DATA")
    left_on = ["year", "mun_id"]  # if "MUN_ID" in index else ["year"]
    merged = pd.merge(votes_and_topics, controls, left_on=left_on, right_index=True)
    # Drop the columns we don't need...
    merged.drop(
        columns=[
            "Unnamed: 0",
            "name",
            "canton_name",
            "mun_name",
            "geoLevelParentnummer",
            "gebietAusgezaehlt",
            "jaStimmenAbsolut",
            "neinStimmenAbsolut",
            "stimmbeteiligungInProzent",
            "eingelegteStimmzettel",
            "anzahlStimmberechtigte",
            "gueltigeStimmen",
            "votedate",
        ],
        inplace=True,
    )
    # ... and prepare for XGBoost
    merged["year"] -= merged["year"].min()
    merged["jaStimmenInProzent"] /= 100
    merged["mun_id"] = merged["mun_id"].astype("category")
    merged["canton_id"] = merged["canton_id"].astype("category")
    return merged


def _preprocess_controls(df: pd.DataFrame, start: int, end: int):
    df.dropna(inplace=True)
    df["YEAR"] = df["YEAR"].astype(int)
    index = ["YEAR", "MUN_ID"] if "MUN_ID" in df.columns else ["YEAR"]
    df = df.pivot(index=index, columns="VALUE", values="DATA")
    if df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(1)
    df.reset_index(inplace=True)
    new_years = set(range(start, end + 1))
    old_years = set(df["YEAR"].unique())
    all_years = sorted(new_years | old_years)
    if "MUN_ID" in df.columns:
        all_muns = df["MUN_ID"].unique()
        mesh = pd.MultiIndex.from_product([all_years, all_muns], names=index)
    else:
        mesh = pd.Index(all_years, name="YEAR")
    new_df = pd.DataFrame(index=mesh).reset_index()
    result = pd.merge(new_df, df, on=index, how="left")
    result = result.melt(id_vars=index, var_name="VALUE", value_name="DATA")
    return result


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: Config) -> None:
    if not cfg.data_dir:
        data_dir = Path(hydra.core.hydra_config.HydraConfig.get().runtime.output_dir)
    else:
        data_dir = Path(cfg.data_dir)

    if not cfg.model_dir:
        model_dir = Path(hydra.core.hydra_config.HydraConfig.get().runtime.output_dir)
    else:
        model_dir = Path(cfg.model_dir)

    intermediate_dir = data_dir / "intermediate"
    controls_dir = intermediate_dir / "controls"

    print("Loading votes...")
    votes_data = _load_votes(cfg.data.votes, intermediate_dir)
    print("Loading topics...")
    topics_data = _load_topics(cfg.data.topics)

    print("Preprocessing votes...")
    votes_and_topics = _preprocess_votes(votes_data, topics_data)
    print("Done preprocessing votes.")

    controls = []
    for i in range(11):
        df = pd.read_parquet(controls_dir / f"socioeconomic_{i}.parquet")
        df = _preprocess_controls(
            df, votes_and_topics["year"].min(), votes_and_topics["year"].max()
        )
        controls.append(df)
    controls = pd.concat(controls)

    print(f"Controls before pivot: {controls.shape}")
    print("Preprocessing controls...")
    X = _preprocess_dataset(controls, votes_and_topics)
    print("Done preprocessing controls.")
    print(f"Data after pivot: {X.shape}")

    train = X[X["id"] < cfg.model.test_cutoff]
    test = X[X["id"] >= cfg.model.test_cutoff]

    dtrain = xgb.DMatrix(
        train.drop(columns=["jaStimmenInProzent"]),
        label=train["jaStimmenInProzent"],
        enable_categorical=True,
    )
    dtest = xgb.DMatrix(
        test.drop(columns=["jaStimmenInProzent"]),
        label=test["jaStimmenInProzent"],
        enable_categorical=True,
    )

    params = {
        # Group 1
        "max_depth": 9,
        "min_child_weight": 0.8,
        # Group 2
        "subsample": 0.6,
        "colsample_bytree": 1.0,
        # Group 3
        "learning_rate": 0.01,
        # Other
        "device": "gpu",
    }
    print(params)
    xgb_model = xgb.train(params, dtrain, 1000)

    print(f"Eval score @ {cfg.model.test_cutoff}: {xgb_model.eval(dtest)}")
    xgb_model.save_model(model_dir / "big_model.model")
    explainer = shap.TreeExplainer(xgb_model)
    explanation = explainer(dtest)
    explanation.feature_names = train.drop(columns=["jaStimmenInProzent"]).columns
    # Fails for some inexplicable reason
    # pickle.dump(explanation, model_dir / "explanation.pkl")


if __name__ == "__main__":
    main()
