import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from scm_analytics import ScmAnalytics, config
from pandas import Series

analytics = ScmAnalytics.ScmAnalytics(config.LHS())

usage_df = analytics.usage.df
po_df = analytics.po.df

start = min(usage_df["start_dt"])
end = max(usage_df["start_dt"])
po_df = po_df[po_df["order_date"] >= start]
po_df = po_df[po_df["order_date"] <= end]
po_df["leadtime_intdays"] = po_df["order_leadtime"].apply(lambda x: x.days)

usage_items = set(usage_df["item_id"])
case_services = set(usage_df[usage_df["case_service"].notna()]["case_service"])
po_items = set(po_df["item_id"])

po_summary_df = po_df.groupby(["item_id"]).agg({
        'po_id': "nunique",
        'qty_ea': 'sum',
        'leadtime_intdays': ['mean', 'std']
    }).reset_index()

po_summary_df.columns = [' '.join(col).strip().replace(" ", "_") for col in po_summary_df.columns.values]
po_summary_df = po_summary_df.rename(columns={"qty_ea_sum": "ordered_qty",
                                              "po_id_nunique": "orders_placed"})

common_items = usage_items.intersection(po_items)
usage_df = usage_df[usage_df["item_id"].isin(common_items)]
po_summary_df = po_summary_df[po_summary_df["item_id"].isin(common_items)]

item_used_lkup = usage_df.groupby(["item_id", "case_service"]).agg({"used_qty": "sum",
                                                                    "code_name": "max",
                                                                    "unit_price": "max"}).reset_index()

item_used_df = item_used_lkup.pivot(index="item_id", columns="case_service", values='used_qty')\
                               .fillna(0)\
                               .reset_index()
item_used_df["total_used_qty"] = item_used_df[[c for c in case_services]].sum(axis=1)
for c in case_services:
    item_used_df[c] = item_used_df[c] / item_used_df["total_used_qty"]

item_info_lkup = usage_df.groupby(["item_id"]).agg({"code_name": "max",
                                                    "unit_price": "max"}).reset_index()

item_used_df = item_used_df.join(item_info_lkup.set_index(["item_id"]),
                                   on="item_id",
                                   how="left",
                                   rsuffix="info")
item_used_df = item_used_df.join(po_summary_df.set_index("item_id"),
                                 on="item_id",
                                 how="left",
                                 rsuffix="po")


item_used_df["used_ordered_ratio"] = item_used_df["total_used_qty"] / item_used_df["ordered_qty"]

item_used_df.to_csv("item_selection.csv")
