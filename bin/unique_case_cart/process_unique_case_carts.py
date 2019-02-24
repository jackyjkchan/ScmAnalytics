from scm_analytics import ScmAnalytics, config
from os import path
# https://stackabuse.com/hierarchical-clustering-with-python-and-scikit-learn/


def create_preference_card_frozensets(data):
    # Takes a case cart DataFrame grouped by case_cart_id or (surgery) event_id
    # and creates a frozen set of (item_id, filled_qty) per case_cart
    return frozenset((item_id, filled_qty) for item_id, filled_qty in zip(data["item_id"], data["fill_qty"]))


if __name__ == "__main__":
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    usage_surgeries = set(analytics.usage.df["event_id"])
    usage_items = set(analytics.usage.df["item_id"])

    case_cart_surgeries = set(analytics.case_cart.df["event_id"])

    # filter to only analyze usage items
    case_cart_df = analytics.case_cart.df
    #case_cart_df = analytics.case_cart.df[analytics.case_cart.df["item_id"].isin(usage_items)]

    preference_card_df = case_cart_df.groupby(["case_cart_id"])\
                                     .apply(create_preference_card_frozensets)\
                                     .reset_index(name='pref_card')

    preference_card_df = preference_card_df.groupby(["pref_card"]).agg({
            'case_cart_id': 'nunique'
    }).reset_index()

    data = list(preference_card_df["case_cart_id"])
    title = "'Pref Card' Usage Distribution"#+" (Filtered on Usage Items Only)"
    analytics.discrete_distribution_plt(data,
                                        save_dir=path.join(config.LHS().results_path),
                                        overflow=20,
                                        show=True,
                                        title=title,
                                        x_label="Times a Preference Card is Used",
                                        y_label="Frequency (Preference Card Count)"
                                        )

