from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.PoMetrics import OrderLeadTimeDiscreteDistribution
from os import path


if __name__ == "__main__":
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    item_df = analytics.classify_usage_items()
    item_df = item_df[item_df["used_qty"] > 200]
    item_ids = list(item_df.head(15)["item_id"])
    item_ids.append("34652")

    for item_id in item_ids:
        surgery_filter = {"dim": "item_id",
                          "op": "eq",
                          "val": item_id}

        for x_units in ["days"]:
            title = "Ordering Lead Time Distribution for item_id={0}" \
                .format(item_id)
            x_label = "Days"
            y_label = "PO Count"

            data = OrderLeadTimeDiscreteDistribution() \
                .set_x_units(x_units) \
                .get_data(analytics.po.df, filters=surgery_filter)

            # analytics.time_distribution_plt(data,
            #                                 x_units,
            #                                 save_dir=path.join(config.LHS().results_path, "test"),
            #                                 title=title,
            #                                 x_label=x_label,
            #                                 y_label=y_label,
            #                                 show=False)
            analytics.discrete_distribution_plt(data,
                                                overflow=30,
                                                save_dir=path.join(config.LHS().results_path, "test"),
                                                show=False,
                                                title=title,
                                                x_label="Order Lead Time Days",
                                                y_label="Frequency PO Count"
                                                )
