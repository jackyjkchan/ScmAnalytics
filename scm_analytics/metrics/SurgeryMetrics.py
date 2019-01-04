from scm_analytics.metrics.BaseMetric import BaseMetric


class DistributionMetric(BaseMetric):
    def __init__(self, usage_df):
        super(DistributionMetric, self).__init__(usage_df)
        self.metric_name = "Distribution"

    def compute_metric(self, df, groupby_dim):
        data = df[[groupby_dim]] \
            .groupby([groupby_dim]) \
            .agg({groupby_dim: 'count'}) \
            .reset_index() \
            .rename(columns={'groupby_dim': 'y', groupby_dim: 'x'})
        return data
