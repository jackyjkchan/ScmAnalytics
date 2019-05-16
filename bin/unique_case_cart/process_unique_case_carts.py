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


if __name__ == "__main__":
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    usage_surgeries = set(analytics.usage.df["event_id"])
    usage_items = set(analytics.usage.df["item_id"])

    case_cart_surgeries = set(analytics.case_cart.df["event_id"])

    # filter to only analyze usage items
    case_cart_df = analytics.case_cart.df

    #case_cart_df = analytics.case_cart.df[analytics.case_cart.df["item_id"].isin(usage_items)]
    case_services = set(case_cart_df[case_cart_df["case_service"].notna()]["case_service"])
    print(case_services)
    for case_service in case_services:
        case_cart_filtered_df = case_cart_df[case_cart_df["case_service"] == case_service]
        preference_card_df = case_cart_filtered_df.groupby(["case_cart_id"])\
                                         .apply(create_preference_card_frozensets_v2)\
                                         .reset_index(name='pref_card')


        preference_card_df = preference_card_df.groupby(["pref_card"]).agg({
                'case_cart_id': ['nunique', 'min']
        }).reset_index()

        preference_card_df.to_csv("preference_card_{0}_(id).csv".format(case_service.replace("/", " ")))

        data = list(preference_card_df["case_cart_id"])
        title = "'Pref Card (item_id)' Usage Distribution (case_service = {0})".format(case_service.replace("/", " "))
        analytics.discrete_distribution_plt(data,
                                            save_dir="./",
                                            overflow=20,
                                            show=False,
                                            title=title,
                                            x_label="Times a Preference Card is Used",
                                            y_label="Frequency (Preference Card Count)"
                                            )

