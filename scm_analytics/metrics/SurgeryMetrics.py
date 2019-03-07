from scm_analytics.metrics.BaseMetric import BaseMetric
import pandas as pd

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


class SurgeriesPerDayDistribution(BaseMetric):
    def __init__(self):
        super(SurgeriesPerDayDistribution, self).__init__()
        self.x_units = "Days"
        self.metric_name_base = "Surgeries Per Day Distribution"
        self.metric_name = "Surgeries Per Day Distribution"
        self.y_label = "Frequency (Count of Days)"
        self.x_label = "Number of Surgeries in a day"

    def compute_metric(self, df, groupby_dim, args=None):
        surgery_df = df
        surgery_df["start_date"] = surgery_df["start_dt"].apply(lambda x: x.date())
        start = min(surgery_df["start_date"])
        end = max(surgery_df["start_date"])

        lkup_df = surgery_df.groupby(["start_date"]) \
                            .agg({"event_id": "nunique"}) \
                            .reset_index()

        data_df = pd.DataFrame()
        data_df["start_date"] = pd.date_range(start=start, end=end, freq='D')
        data_df["start_date"] = data_df["start_date"].apply(lambda x: x.date())
        data_df = data_df.join(lkup_df[["start_date", "event_id"]].set_index(["start_date"]),
                               on="start_date",
                               how="left",
                               rsuffix="surgery").fillna(0)
        # i think im missing a groupby here
        return data_df["event_id"].rename(columns={"event_id": 'y'})

    def set_item_id(self, item_id):
        self.item_id = item_id
        self.metric_name = self.metric_name_base + " id " + str(item_id)


class SurgeryCount(BaseMetric):
    def __init__(self):
        super(SurgeryCount, self).__init__()
        self.metric_name = "Surgery count"

    def compute_metric(self, df, groupby_dim, args=None):
        data = df[[groupby_dim, "event_id"]] \
            .groupby([groupby_dim]) \
            .agg({'event_id': 'nunique'}) \
            .reset_index() \
            .rename(columns={'event_id': 'y', groupby_dim: 'x'})
        return data


class SurgeryHours(BaseMetric):
    def __init__(self):
        super(SurgeryHours, self).__init__()
        self.metric_name = "Surgery Hours"

    def compute_metric(self, df, groupby_dim, args=None):
        df = df[df["surgery_duration"].notna()]
        data = df[[groupby_dim, "surgery_duration"]] \
            .groupby([groupby_dim]) \
            .agg({'surgery_duration': 'sum'}) \
            .reset_index() \
            .rename(columns={'surgery_duration': 'y', groupby_dim: 'x'})
        # to convert from seconds to hours
        data["y"] = data["y"].apply(lambda x: x.days*24 + x.seconds / 60)
        return data
