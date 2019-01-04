from scm_analytics.profiles.BaseProfile import BaseProfile
from scm_analytics.metrics.UsageMetrics import *


class UsageProfile(BaseProfile):

    def __init__(self, usage_df):
        super(UsageProfile, self).__init__(usage_df)

        self.mandatory_columns = [
            "event_id",
            "item_id",
            "code_name",
            "used_qty",
            "unit_price",
            "case_service",
            "urgent_elective",
            "booking_dt",
            "start_dt",
            "supply_issue_desc"
        ]

        self.additional_columns = [
            "OR_delay_desc",
            "kmean_label",
            "booking_leadtime"
        ]

        # import all metrics
        self.total_used_qty_metric = TotalUsedQtyMetric()
        self.booking_leadtime_distribution = BookingLeadtimeDistribution()
        self.surgery_inter_arrival_distribution = InterArrivalDistribution()

        self.assert_structure()
        self.preprocess_columns()

    def preprocess_columns(self):
        self.df['booking_leadtime'] = self.df['start_dt'] - self.df['booking_dt']
