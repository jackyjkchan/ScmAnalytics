from scm_analytics import ScmAnalytics, config
from os import path


def main():
    num_clusters = 12
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())
    item_df = analytics.classify_usage_items()
    item_df = item_df[item_df["used_qty"] > 200]
    item_ids = list(item_df.head(15)["item_id"])

    surg_item_usage_df = analytics.kcluster_surgeries(item_ids, k=num_clusters)

    for item_id in item_ids:
        filter_dict = {"dim": "item_id",
                       "op": "eq",
                       "val": item_id
                       }

        analytics.metrics_barchart(analytics.usage.df,
                                   analytics.usage.total_used_qty_metric,
                                   "kmean_label",
                                   filters=filter_dict,
                                   save_dir=path.join(config.LHS().results_path, "test"),
                                   show=True
                                   )

        analytics.metrics_barchart(analytics.usage.df,
                                   analytics.usage.total_used_qty_metric,
                                   "case_service",
                                   filters=filter_dict,
                                   save_dir=path.join(config.LHS().results_path, "test")
                                   )
    return 0


if __name__ == "__main__":
    main()
