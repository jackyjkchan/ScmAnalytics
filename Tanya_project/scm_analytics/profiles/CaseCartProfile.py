from scm_analytics.profiles.BaseProfile import BaseProfile
from scm_analytics.metrics.PoMetrics import *


class CaseCartProfile(BaseProfile):

    def __init__(self, usage_df):
        super(CaseCartProfile, self).__init__(usage_df)

        self.mandatory_columns = [
            "case_cart_id",
            "event_id",
            "item_id",
            "fill_qty",
            "open_qty",
            "hold_qty"
        ]

        self.additional_columns = [
            "scheduled_procedures"
        ]

        self.assert_structure()
        #self.preprocess_columns()

    #def preprocess_columns(self):
    #    self.df['order_leadtime'] = self.df['delivery_date'] - self.df['order_date']
