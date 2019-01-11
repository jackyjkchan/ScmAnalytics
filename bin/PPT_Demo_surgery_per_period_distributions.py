from scm_analytics import ScmAnalytics, config
from os import path
import pandas as pd


if __name__ == "__main__":

    dim = "scheduled_procedures"
    val = "Hernia Hiatus Repair Laparoscopic"




    fn = "Surgery Frequency Distribution {0} = {1}.svg".format(dim, val)
    title = "Distribution of surgeries per day: {0} = {1}".format(dim, val)

    num_clusters = 12
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    item_df = analytics.classify_usage_items()
    item_df = item_df[item_df["used_qty"] > 200]
    item_ids = list(item_df.head(15)["item_id"])

    surg_item_usage_df = analytics.kcluster_surgeries(item_ids, k=num_clusters)

    analytics.usage.df["start_date"] = analytics.usage.df["start_dt"].apply(lambda x: x.date())

    start = min(analytics.usage.df["start_date"])
    end = max(analytics.usage.df["start_date"])

    lkup_df = analytics.usage.df[analytics.usage.df[dim] == val]\
        .groupby(["start_date"])\
        .agg({"event_id": "nunique"})\
        .reset_index()\
        .rename(columns={"event_id": "count"})

    data_df = pd.DataFrame()
    data_df["start_date"] = pd.date_range(start=start, end=end, freq='D')
    data_df["start_date"] = data_df["start_date"].apply(lambda x: x.date())

    data_df = data_df.join(lkup_df[["start_date", "count"]].set_index(["start_date"]),
                           on="start_date",
                           how="left",
                           rsuffix="surgery").fillna(0)

    print(data_df.groupby(["count"])\
          .agg({"start_date": "count"})\
          .reset_index()
          )

    analytics.discrete_distribution_plt(data_df["count"],
                                        save_dir=path.join(config.LHS().results_path, fn),
                                        show=True,
                                        title=title,
                                        x_label="Surgeries per Day",
                                        y_label="Frequency"
                                        )
