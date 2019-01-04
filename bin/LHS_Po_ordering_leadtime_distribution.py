from scm_analytics import ScmAnalytics, config


if __name__ == "__main__":
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    item_df = analytics.classify_usage_items()
    item_df = item_df[item_df["used_qty"] > 200]
    item_ids = list(item_df.head(15)["item_id"])

    for item_id in item_ids:
        surgery_filter = {"dim": "item_id",
                          "op": "eq",
                          "val": item_id}

        for x_units in ["days"]:#, "hours", "weeks"]:
            analytics.po.ordering_leadtime_distribution.set_x_units(x_units)
            analytics.distribution_plot(analytics.po.df,
                                        analytics.po.ordering_leadtime_distribution,
                                        filter_dict=surgery_filter,
                                        save_dir=config.LHS().results_path,
                                        show=False)
