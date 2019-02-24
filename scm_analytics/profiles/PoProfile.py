from scm_analytics.profiles.BaseProfile import BaseProfile
from scm_analytics.metrics.PoMetrics import *


class PoProfile(BaseProfile):

    def __init__(self, usage_df):
        super(PoProfile, self).__init__(usage_df)

        self.mandatory_columns = [
            "po_id",
            "order_date",
            "po_class",
            "item_id",
            "qty",
            "unit_of_measure",
            "unit_price",
            "delivery_date",
            "qty_ea"
        ]

        self.additional_columns = [
            "order_leadtime"
        ]

        self.assert_structure()
        self.preprocess_columns()

    def preprocess_columns(self):
        self.df['order_leadtime'] = self.df['delivery_date'] - self.df['order_date']
