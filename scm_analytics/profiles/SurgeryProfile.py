from scm_analytics.profiles.BaseProfile import BaseProfile
from scm_analytics.metrics.UsageMetrics import *


class SurgeryProfile(BaseProfile):

    def __init__(self, surgery_df):
        super(SurgeryProfile, self).__init__(surgery_df)

        self.mandatory_columns = [
            "event_id",
            "scheduled_procedures",
            "completed_procedures",
            "case_service",
            "OR_delay_desc",
            "start_dt",
            "end_dt",
            "case_dt",
            "booking_dt",
            "case_cart_id",
            "urgent_elective"
        ]

        # import all metrics
        self.total_used_qty_metric = TotalUsedQtyMetric()

        self.assert_structure()
        self.preprocess_columns()

    def preprocess_columns(self):
        self.df['booking_leadtime'] = self.df['case_dt'] - self.df['booking_dt']
