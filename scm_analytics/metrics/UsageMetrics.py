from scm_analytics.metrics.BaseMetric import BaseMetric
import pandas as pd


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


class BookingLeadTimeDistribution(BaseMetric):
    def __init__(self):
        super(BookingLeadTimeDistribution, self).__init__()
        self.x_units = "days"
        self.metric_name = "Booking Leadtime Distribution"
        self.y_label = "Count of Surgeries"
        self.x_label = "Booking Lead Time ({0})".format(self.x_units)

    def compute_metric(self, df, groupby_dim, args=None):
        df = df.groupby(["event_id"])\
            .agg({"booking_leadtime": "max"})\
            .reset_index()
        data = df[["booking_leadtime"]]\
            .rename(columns={'booking_leadtime': 'y'})
        return data['y']

    def set_x_units(self, units):
        assert (units in ["days", "weeks", "4hours", "1hours", "halfhours"])
        self.x_units = units
        self.x_label = "Booking Lead Time ({0})".format(self.x_units)
        return self


class InterArrivalTimeDistribution(BaseMetric):
    def __init__(self):
        super(InterArrivalTimeDistribution, self).__init__()
        self.x_units = "days"
        self.metric_name = "Surgery Inter Arrival Distribution"
        self.y_label = "Count of Surgeries"
        self.x_label = "Booking Leadtime ({0})".format(self.x_units)

    def compute_metric(self, df, groupby_dim, args=None):
        df = df.groupby(["event_id"])\
            .agg({"start_dt": "max"})\
            .reset_index().sort_values(["start_dt"])
        df["inter_arrival_time"] = df["start_dt"].diff()
        data = df[df["inter_arrival_time"].notna()][["inter_arrival_time"]]\
            .rename(columns={'inter_arrival_time': 'y'})
        return data['y']

    def set_x_units(self, units):
        assert (units in ["days", "weeks", "4hours", "1hours", "halfhours"])
        self.x_units = units
        self.x_label = "Surgery Start Dt Inter Arrival ({0})".format(self.x_units)
        return self


# class ItemUsageDistribution(BaseMetric):
#     def __init__(self):
#         super(ItemUsageDistribution, self).__init__()
#         self.x_units = "Units"
#         self.metric_name_base = "Item Usage Distribution"
#         self.metric_name = "Item Usage Distribution"
#         self.y_label = "Count of Surgeries"
#         self.x_label = "Number of items used ({0})".format(self.x_units)
#         self.item_id = None
#
#     def compute_metric(self, df, groupby_dim, args=None):
#         data = df[[self.item_id]]\
#             .rename(columns={self.item_id: 'y'})
#
#         return data
#
#     def set_item_id(self, item_id):
#         self.item_id = item_id
#         self.metric_name = self.metric_name_base + " id " + str(item_id)


class ItemUsagePerDayDistribution(BaseMetric):
    def __init__(self):
        super(ItemUsagePerDayDistribution, self).__init__()
        self.x_units = "days"
        self.metric_name_base = "Item Usage Per Day Distribution"
        self.metric_name = "Item Usage Per Day Distribution"
        self.y_label = "Frequency (Number of Days)"
        self.x_label = "Number of items used ({0})".format(self.x_units)
        self.item_id = None

    def compute_metric(self, df, groupby_dim, args={}):
        usage_df = df
        if len(usage_df) == 0:
            return [0]
        usage_df["start_date"] = usage_df["start_dt"].apply(lambda x: x.date())
        start = args["start"] if "start" in args else min(usage_df["start_date"])
        end = args["end"] if "end" in args else max(usage_df["start_date"])

        lkup_df = usage_df[usage_df["item_id"] == self.item_id] \
            .groupby(["start_date"]) \
            .agg({"used_qty": "sum"}) \
            .reset_index()

        if len(lkup_df) == 0:
            return [0]

        data_df = pd.DataFrame()
        data_df["start_date"] = pd.date_range(start=start, end=end, freq='D')
        data_df["start_date"] = data_df["start_date"].apply(lambda x: x.date())
        data_df = data_df.join(lkup_df[["start_date", "used_qty"]].set_index(["start_date"]),
                               on="start_date",
                               how="left",
                               rsuffix="surgery").fillna(0)
        return data_df["used_qty"].rename(columns={self.item_id: 'y'})

    def set_item_id(self, item_id):
        self.item_id = item_id
        self.metric_name = self.metric_name_base + " id " + str(item_id)
        return self


class ItemUsagePerWeekDistribution(BaseMetric):
    def __init__(self):
        super(ItemUsagePerWeekDistribution, self).__init__()
        self.x_units = "weeks"
        self.metric_name_base = "Item Usage Per Week Distribution"
        self.metric_name = "Item Usage Per Week Distribution"
        self.y_label = "Frequency (Number of Weeks)"
        self.x_label = "Number of items used ({0})".format(self.x_units)
        self.item_id = None

    def compute_metric(self, df, groupby_dim, args=None):
        usage_df = df
        usage_df["start_date"] = usage_df["start_dt"].\
            apply(lambda x: "{0}-{1}".format(str(x.year-1 if (x.month == 1 and x.week == 52) else x.year),
                                             str(x.week)))
        usage_df = usage_df[usage_df["start_date"] != "nan-nan"]
        start = min(usage_df["start_date"])
        end = max(usage_df["start_date"])

        lkup_df = usage_df[usage_df["item_id"] == self.item_id] \
            .groupby(["start_date"]) \
            .agg({"used_qty": "sum"}) \
            .reset_index()

        data_df = pd.DataFrame()
        data_df["start_date"] = list(set(usage_df["start_date"]))
        data_df = data_df.join(lkup_df[["start_date", "used_qty"]].set_index(["start_date"]),
                               on="start_date",
                               how="left",
                               rsuffix="usage").fillna(0)
        return data_df["used_qty"].rename(columns={self.item_id: 'y'})

    def set_item_id(self, item_id):
        self.item_id = item_id
        self.metric_name = self.metric_name_base + " id " + str(item_id)
        return self
