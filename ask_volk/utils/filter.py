from ask_volk.config.data import Filter as FilterConfig


class Filter:
    """Filter for a DataFrame."""

    def __init__(self, config: FilterConfig):
        """Initialize the filter."""
        if not isinstance(config, FilterConfig):
            config = FilterConfig(**config)
        self.config = config

    def apply(self, df):
        """Apply the filter to the DataFrame."""
        key, op, value = self.config.as_tuple()
        return df.loc[op(df[key], value)]
