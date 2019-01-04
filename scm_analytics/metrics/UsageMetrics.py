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


class BookingLeadtimeDistribution(BaseMetric):
    def __init__(self):
        super(BookingLeadtimeDistribution, self).__init__()
        self.x_units = "days"
        self.metric_name = "Booking Leadtime Distribution"
        self.y_label = "Count of Surgeries"
        self.x_label = "Booking Leadtime ({0})".format(self.x_units)

    def compute_metric(self, df, groupby_dim, args=None):
        seconds_in_hr = 60*60
        df = df.groupby(["event_id"])\
            .agg({"booking_leadtime": "max"})\
            .reset_index()
        data = df[["booking_leadtime"]]\
            .rename(columns={'booking_leadtime': 'y'})
        if args:
            if args["x_unit"] == "days":
                data["y"] = data["y"].dt.days
            elif args["x_unit"] == "weeks":
                data["y"] = data["y"].dt.days / 7
            elif args["x_unit"] in ["4hours", "halfhours", "1hours", "hours"]:
                data["y"] = data["y"].dt.days * 24 + data["y"].dt.seconds / seconds_in_hr
            else:
                data["y"] = data["y"].dt.days
            print("DATA points:", len(data["y"]))
        return data

    def set_x_units(self, units):
        assert(units in ["days", "hours", "weeks", "none", "4hours", "1hours", "halfhours"])
        self.x_units = units
        self.x_label = "Booking Leadtime ({0})".format(self.x_units)


class InterArrivalDistribution(BaseMetric):
    def __init__(self):
        super(InterArrivalDistribution, self).__init__()
        self.x_units = "days"
        self.metric_name = "Surgery Inter Arrival Distribution"
        self.y_label = "Count of Surgeries"
        self.x_label = "Booking Leadtime ({0})".format(self.x_units)

    def compute_metric(self, df, groupby_dim, args=None):
        seconds_in_hr = 60*60
        df = df.groupby(["event_id"])\
            .agg({"start_dt": "max"})\
            .reset_index().sort_values(["start_dt"])
        df["inter_arrival_time"] = df["start_dt"].diff()
        data = df[df["inter_arrival_time"].notna()][["inter_arrival_time"]]\
            .rename(columns={'inter_arrival_time': 'y'})

        if args:
            if args["x_unit"] == "days":
                data["y"] = data["y"].dt.days
            elif args["x_unit"] == "weeks":
                data["y"] = data["y"].dt.days / 7
            elif args["x_unit"] in ["4hours", "halfhours", "1hours", "hours"]:
                data["y"] = data["y"].dt.days * 24 + data["y"].dt.seconds / seconds_in_hr
            else:
                data["y"] = data["y"].dt.days
            print("DATA points:", len(data["y"]))
        return data

    def set_x_units(self, units):
        assert (units in ["days", "hours", "weeks", "none", "4hours", "1hours", "halfhours"])
        self.x_units = units
        self.x_label = "Surgery Start Dt Inter Arrival ({0})".format(self.x_units)
