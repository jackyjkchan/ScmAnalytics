from scm_analytics import ScmAnalytics, config
from os import path


# https://stackabuse.com/hierarchical-clustering-with-python-and-scikit-learn/


def create_preference_card_frozensets(data):
    # Takes a case cart DataFrame grouped by case_cart_id or (surgery) event_id
    # and creates a frozen set of (item_id, filled_qty) per case_cart
    return frozenset((item_id, filled_qty) for item_id, filled_qty in zip(data["item_id"], data["fill_qty"]))


def create_preference_card_frozensets_v2(data):
    # Takes a case cart DataFrame grouped by case_cart_id or (surgery) event_id
    # and creates a frozen set of (item_id, filled_qty) per case_cart
    return frozenset(item_id for item_id, filled_qty in zip(data["item_id"], data["fill_qty"]))


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

usage_surgeries = set(analytics.usage.df["event_id"])
usage_items = set(analytics.usage.df["item_id"])

case_cart_surgeries = set(analytics.case_cart.df["event_id"])

case_services = set(case_cart_df[case_cart_df["case_service"].notna()]["case_service"])

for case_service in case_services:
    items = []
    df = case_cart_df[case_cart_df["case_service"] == case_service]
    while len(df) > 0:
        item_id = df.groupby(["item_id"]) \
            .agg({"event_id": "nunique"}) \
            .reset_index() \
            .sort_values(["event_id"], ascending=[0]).iloc[0]["item_id"]
        items.append(item_id)
        events = set(df[df["item_id"] == item_id]["event_id"])
        df = df[~df["event_id"].isin(events)]


    case_cart_filtered_df = case_cart_df[case_cart_df["item_id"].isin(items)]

    preference_card_df = case_cart_filtered_df.groupby(["case_cart_id"])\
                                             .apply(create_preference_card_frozensets_v2)\
                                             .reset_index(name='pref_card')

    preference_card_df = preference_card_df.groupby(["pref_card"]).agg({
            'case_cart_id': 'nunique'
    }).reset_index()

    preference_card_df.to_csv("prefCard_id_usages_caseService_{0}.csv".format(case_service.replace("/", " ")))

    data = list(preference_card_df["case_cart_id"])

    title = "'Greedy Item Select Pref Card (item_id)' Usage Distribution (case_service = {0})"\
        .format(case_service.replace("/", " "))

    analytics.discrete_distribution_plt(data,
                                        save_dir="./",
                                        overflow=20,
                                        show=False,
                                        title=title,
                                        x_label="Times a Preference Card is Used",
                                        y_label="Frequency (Preference Card Count)"
                                        )
