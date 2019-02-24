from scm_analytics import ScmAnalytics, config
from os import path
import re
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    pattern = "hernia.*repair"
    surgery_filter = {"dim": "scheduled_procedures",
                      "op": "eq",
                      "val": "Hernia Hiatus Repair Laparoscopic"}

    num_clusters = 12
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())
    item_df = analytics.classify_usage_items()
    item_df = item_df[item_df["used_qty"] > 2000]
    print(item_df)
    item_ids = list(item_df.head(15)["item_id"])
    X, surg_item_usage_df = analytics.process_surg_vectors(item_ids, filter_zeros=False)
    surg_item_usage_df = surg_item_usage_df.join(analytics.surgery.df[["event_id",
                                                                     "scheduled_procedures"]
                                                                    ].set_index("event_id"),
                                                 on="event_id",
                                                 how="left",
                                                 rsuffix="_procedures"
                                                 )

    for item_id in item_ids:
        df = analytics.process_filters(surg_item_usage_df, [surgery_filter])
        data = df[item_id]
        title = "{0} Item Usage Distribution of Item {1}".format(surgery_filter["val"], item_id)
        fn = "{0}.svg".format(title)
        analytics.discrete_distribution_plt(data,
                                            save_dir=config.LHS().results_path,
                                            show=True,
                                            title=title,
                                            x_label="Count of Items Used",
                                            y_label="Frequency (Surgeries Count)"
                                            )



