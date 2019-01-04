from scm_analytics import ScmAnalytics, config
import matplotlib.pyplot as plt
from os import path

def main():
    num_clusters = 12
    num_items = [15, 25, 50]

    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    item_df = analytics.classify_usage_items()
    item_df = item_df[item_df["used_qty"] > 200]
    for num_item in num_items:
        print("processing:", num_item)
        item_ids = list(item_df.head(num_item)["item_id"])
        label = "{0} items".format(num_item)
        analytics.kcluster_elbow_plot(item_ids, label=label, show=False, normalized=True)
    plt.show()
    return 0


if __name__ == "__main__":
    main()
