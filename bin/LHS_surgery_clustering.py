from scm_analytics import ScmAnalytics, config
from os import path


if __name__ == "__main__":
    num_clusters = 12
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())
    item_df = analytics.classify_usage_items()
    item_df = item_df[item_df["used_qty"] > 200]
    print(item_df)
    item_ids = list(item_df.head(15)["item_id"])

    surg_item_usage_df = analytics.kcluster_surgeries(item_ids, k=num_clusters)

    for kmean_label in range(0, num_clusters):
        surgery_filter = {"dim": "kmean_label",
                          "op": "eq",
                          "val": kmean_label}

        for x_units in ["days", "hours", "weeks"]:
            analytics.usage.booking_leadtime_distribution.set_x_units(x_units)
            analytics.distribution_plot(analytics.usage.df,
                                        analytics.usage.booking_leadtime_distribution,
                                        filters=surgery_filter,
                                        #save_dir=config.LHS().results_path,
                                        save_dir=path.join(config.LHS().results_path, "test"),
                                        show=False)
