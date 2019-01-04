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


class OrderLeadtimeDistribution(BaseMetric):
    def __init__(self):
        super(OrderLeadtimeDistribution, self).__init__()
        self.x_units = "days"
        self.metric_name = "Order Leadtime Distribution"
        self.y_label = "Count of PO Ids"
        self.x_label = "Order Leadtime ({0})".format(self.x_units)

    def compute_metric(self, df, groupby_dim, args=None):
        seconds_in_hr = 60*60
        data = df[["order_leadtime"]]\
            .rename(columns={'order_leadtime': 'y'})
        if args:
            if args["x_unit"] == "days":
                data["y"] = data["y"].dt.days
            elif args["x_unit"] == "weeks":
                data["y"] = data["y"].dt.days / 7
            elif args["x_unit"] == "hours":
                data["y"] = data["y"].dt.days + data["y"].dt.seconds / seconds_in_hr
            else:
                data["y"] = data["y"].dt.days
            print("DATA points:", len(data["y"]))
        return data

    def set_x_units(self, units):
        assert(units in ["days", "hours", "weeks", "none"])
        self.x_units = units
        self.x_label = "Order Leadtime ({0})".format(self.x_units)
