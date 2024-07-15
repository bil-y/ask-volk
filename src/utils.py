import pandas as pd


def get_top_n(df, n):
    # Get the indices of the top n values for each row
    top_n_indices = df.apply(lambda row: row.nlargest(n).index, axis=1)

    # Create a new DataFrame, where all but top n are set to zero
    binary_df = pd.DataFrame(0, index=df.index, columns=df.columns, dtype="float")
    for idx, indices in enumerate(top_n_indices):
        binary_df.loc[idx, indices] = df.loc[idx, indices]
    return binary_df


def pre_process_topics(topics: pd.DataFrame, mode: str, **kwargs) -> pd.DataFrame:
    """Function that takes raw topics as dataframes and returns preprocessed topics again as a dataframe

    Three different modes:
    - cutoff: given the threshold keyword argument (default = 0), all values for topics shares below
        that threshold are set to this value
    - highest: given n as the number keyword argument of topics (default = 1), the n topics with
        highest shares are kept and the others are set to zero
    - drop: columns specified in keyword argument columns are dropped
    """
    if mode == "cutoff":
        threshold = kwargs["threshold"]
        topics = pd.concat(
            [topics.drop(columns=["id"]).clip(lower=threshold), topics["id"]], axis=1
        )
    elif mode == "highest":
        number = kwargs["number"]
        top_n_df = get_top_n(topics.drop(columns=["id"]), number)
        topics = pd.concat([top_n_df, topics["id"]], axis=1)
    elif mode == "drop":
        columns = kwargs["columns"]
        topics = topics.drop(columns=columns)
    else:
        raise ValueError("mode must be one of: 'cutoff', 'highest', 'drop'")
    return topics
