from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.UsageMetrics import BookingLeadTimeDistribution
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

        for x_units in ["days", "1hours", "weeks", "halfhours"]:
            title = "Booking Lead Time Distribution for [{0}] Surgeries ({1} Bins)" \
                .format(analytics.filter_desc(surgery_filter), x_units)
            x_label = "{0} Bins".format(x_units)
            y_label = "Surgery Count"

            data = BookingLeadTimeDistribution() \
                .set_x_units(x_units) \
                .get_data(analytics.usage.df, filters=surgery_filter)
            analytics.time_distribution_plt(data,
                                            x_units,
                                            save_dir=path.join(config.LHS().results_path, "test"),
                                            title=title,
                                            x_label=x_label,
                                            y_label=y_label,
                                            show=False)
