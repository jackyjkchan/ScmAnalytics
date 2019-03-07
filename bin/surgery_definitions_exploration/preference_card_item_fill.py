from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.UsageMetrics import TotalUsedQtyMetric
import pandas as pd


"""this is a per item definition of surgeries. We look for all preference cards that consist of the same fill_qty for the
item id of interest. 
To test this definition of a surgery we will need to look for common items between case_cart and usage. See how many
uses of the item is undocumented by case_carts etc
"""

analytics = ScmAnalytics.ScmAnalytics(config.LHS())

common_events = set(analytics.usage.df["event_id"])\
    .intersection(set(analytics.case_cart.df["event_id"]))
case_cart_df = analytics.case_cart.df[analytics.case_cart.df["event_id"].isin(common_events)]
usage_df = analytics.usage.df[analytics.usage.df["event_id"].isin(common_events)]
po_df = analytics.po.df

start = min(usage_df["start_dt"])
end = max(usage_df["start_dt"])
po_df = po_df[po_df["order_date"] >= start]
po_df = po_df[po_df["order_date"] <= end]
po_df["leadtime_intdays"] = po_df["order_leadtime"].apply(lambda x: x.days)

case_cart_items = set(case_cart_df["item_id"])
usage_items = set(usage_df["item_id"])
po_items = set(po_df["item_id"])
po_summary_df = po_df.groupby(["item_id"]).agg({
        'po_id': "nunique",
        'qty_ea': 'sum',
        'leadtime_intdays': ['mean', 'std']
    }).reset_index()
po_summary_df.columns = [' '.join(col).strip().replace(" ", "_") for col in po_summary_df.columns.values]
po_summary_df = po_summary_df.rename(columns={"qty_ea_sum": "ordered_qty",
                                              "po_id_nunique": "orders_placed"})

common_items = usage_items.intersection(case_cart_items).intersection(po_items)
case_cart_df = case_cart_df[case_cart_df["item_id"].isin(common_items)]
usage_df = usage_df[usage_df["item_id"].isin(common_items)]
po_summary_df = po_summary_df[po_summary_df["item_id"].isin(common_items)]


item_filled_lkup = case_cart_df.groupby(["item_id"]).agg({"fill_qty": "sum"}).reset_index()
item_used_lkup = usage_df.groupby(["item_id"]).agg({"used_qty": "sum",
                                                    "code_name": "max",
                                                    "unit_price": "max"}).reset_index()

item_df = item_filled_lkup.join(item_used_lkup.set_index("item_id"),
                                on="item_id",
                                how="left",
                                rsuffix="usage")
item_df = item_df.join(po_summary_df.set_index("item_id"),
                                on="item_id",
                                how="left",
                                rsuffix="po")

item_df["used_filled_ratio"] = item_df["used_qty"] / item_df["fill_qty"]
item_df["used_ordered_ratio"] = item_df["used_qty"] / item_df["ordered_qty"]
item_df.to_csv("item_filled_usage_ratio.csv")

case_cart_cleaned_df = case_cart_df.groupby(["event_id", "item_id"]).agg({"fill_qty": "max"}).reset_index()
usage_labeled_df = usage_df.join(case_cart_cleaned_df[["event_id", "item_id", "fill_qty"]]
                                 .set_index(["event_id", "item_id"]),
                                 on=["event_id", "item_id"],
                                 how="left",
                                 rsuffix="case_cart").fillna(0)

usage_cleaned_df = usage_labeled_df.groupby(["event_id", "item_id"]).agg({"fill_qty": "max",
                                                                          "code_name": "max",
                                                                          "used_qty": "max"
                                                                          }).reset_index()


# extract surgery definitions for each item and dump usage distributions.
for item_id in item_df[item_df["used_qty"] > 200]["item_id"]:
    data = pd.DataFrame()
    data["event_id"] = list(set(usage_df["event_id"]))
    data = data.join(usage_cleaned_df[usage_cleaned_df["item_id"] == item_id]
                     [["event_id", "used_qty", "fill_qty"]].set_index("event_id"),
                     on="event_id",
                     how="left",
                     rsuffix="usage"
                     ).fillna(0)
    for label in set(data["fill_qty"]):
        d = data[data["fill_qty"] == label]
        title = "Usage_Distribution_By_Surgeries_Per_Label[item_id={0}][label_filled_qty={1}]".format(item_id,
                                                                                                      str(int(label)))
        analytics.discrete_distribution_plt(d["used_qty"],
                                            title=title,
                                            save_dir="filled_qty_as_label",
                                            x_label="Usages Per Surgery",
                                            y_label="Frequency (Surgery Count)")

    order = list(set(data["fill_qty"]))
    order.sort()
    # order = [str(x) for x in order]
    title = "Total_Usage_By_Surgeries_Labels[item_id={0}]]".format(item_id)
    analytics.metrics_barchart(data,
                               TotalUsedQtyMetric(),
                               "fill_qty",
                               title=title,
                               save_dir="filled_qty_as_label",
                               order=order)
