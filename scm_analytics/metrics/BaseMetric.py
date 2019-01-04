import re

class BaseMetric:
    def __init__(self):
        return

    def filter_df(self, df, filter_dict):
        if filter_dict["op"] in ["eq", "=="]:
            df = df[df[filter_dict["dim"]] == filter_dict["val"]]
        elif filter_dict["op"] == "re":
            pattern = filter_dict["val"]
            df = df[df[filter_dict["dim"]].apply(lambda x: bool(re.search(pattern.lower(), str(x).lower())))]
        return df

    def get_data(self, df, groupby_dim=None, filter_dict=None, args=None):
        if groupby_dim:
            df = df[df[groupby_dim].notna()]
        if filter_dict:
            df = self.filter_df(df, filter_dict)
        return self.compute_metric(df, groupby_dim, args=args)

    def compute_metric(self, df, groupby_dim, args=None):
        data = df[[groupby_dim, "used_qty"]] \
            .groupby([groupby_dim]) \
            .agg({'used_qty': 'sum'}) \
            .reset_index() \
            .rename(columns={'used_qty': 'y', groupby_dim: 'x'})
        return data
