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
        #self.booking_leadtime_distribution = BookingLeadTimeDistribution()
        #self.item_usage_distribution = ItemUsageDistribution()

        self.assert_structure()
        self.preprocess_columns()

    def preprocess_columns(self):
        self.df['booking_leadtime'] = self.df['start_dt'] - self.df['booking_dt']

    def get_pref_item_fill_surgery_labels(self, item_id, case_cart_df):
        usage_filtered_df = self.df[self.df["item_id"] == item_id]
        usage_filtered_df = usage_filtered_df[usage_filtered_df["start_dt"].notna()]
        usage_events = set(usage_filtered_df["event_id"])
        case_cart_filtered_df = case_cart_df[case_cart_df["item_id"] == item_id]
        case_cart_filtered_df = case_cart_filtered_df[case_cart_filtered_df["event_id"].isin(usage_events)]

        usage_cleaned_df = usage_filtered_df.groupby(["event_id", "item_id"]).agg({"code_name": "max",
                                                                                   "used_qty": "max",
                                                                                   "start_dt": "max",
                                                                                   "urgent_elective": "max"
                                                                                   }).reset_index()
        case_cart_cleaned_df = case_cart_filtered_df.groupby(["event_id", "item_id"]).agg({"fill_qty": "max"}
                                                                                          ).reset_index()
        usage_cleaned_df = usage_cleaned_df.join(case_cart_cleaned_df.set_index(["event_id"]),
                                                 on="event_id",
                                                 how="outer",
                                                 rsuffix="case_cart").fillna(0)
        return usage_cleaned_df

    def label_events_with_pref_item_fill_qty(self, item_id, case_cart_df, df_to_label):
        events = set(df_to_label["event_id"])
        case_cart_filtered_df = case_cart_df[case_cart_df["item_id"] == item_id]
        case_cart_filtered_df = case_cart_filtered_df[case_cart_filtered_df["event_id"].isin(events)]

        case_cart_cleaned_df = case_cart_filtered_df.groupby(["event_id"])\
                                                    .agg({"fill_qty": "max"})\
                                                    .reset_index()
        df_to_label = df_to_label.join(case_cart_cleaned_df[["event_id", "fill_qty"]].set_index(["event_id"]),
                                                 on="event_id",
                                                 how="outer",
                                                 rsuffix="case_cart").fillna(0)
        return df_to_label




