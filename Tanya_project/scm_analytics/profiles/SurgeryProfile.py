from scm_analytics.profiles.BaseProfile import BaseProfile
from scm_analytics.metrics.UsageMetrics import *
import datetime


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

    def process_day_of_week_column(self):
        weekday_map = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday"
        }

        self.df['day_of_week'] = self.df['case_dt'].apply(lambda x:
                                                          weekday_map[x.weekday()]
                                                          if x.weekday() in weekday_map
                                                          else "Unknown")

    def process_month_column(self):
        self.df['month'] = self.df['case_dt'].apply(lambda x: str(x.month))

    def process_surgery_duration(self):
        self.df['surgery_duration'] = self.df["end_dt"] - self.df["start_dt"]
