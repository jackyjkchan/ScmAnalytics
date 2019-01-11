from scm_analytics.metrics.BaseMetric import BaseMetric


class TotalUsedQtyMetric(BaseMetric):
    def __init__(self):
        super(TotalUsedQtyMetric, self).__init__()
        self.metric_name = "item usage count"

    def compute_metric(self, df, groupby_dim, args=None):
        data = df[[groupby_dim, "used_qty"]] \
            .groupby([groupby_dim]) \
            .agg({'used_qty': 'sum'}) \
            .reset_index() \
            .rename(columns={'used_qty': 'y', groupby_dim: 'x'})
        return data


class OrderLeadTimeDiscreteDistribution(BaseMetric):
    def __init__(self):
        super(OrderLeadTimeDiscreteDistribution, self).__init__()
        self.x_units = "days"
        self.metric_name = "Order Lead Time Distribution"
        self.y_label = "Count of PO Ids"
        self.x_label = "Order Lead Time ({0})".format(self.x_units)

    def compute_metric(self, df, groupby_dim, args=None):
        return df["order_leadtime"].dt.days

    def set_x_units(self, units):
        assert(units in ["days", "1hours", "weeks"])
        self.x_units = units
        self.x_label = "Order Lead Time ({0})".format(self.x_units)
        return self
