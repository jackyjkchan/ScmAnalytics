from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.SurgeryMetrics import SurgeriesPerDayDistribution
import numpy as np

item_ids = ["38197", "85321", "76057"]
analytics = ScmAnalytics.ScmAnalytics(config.LHS())

for item_id in ["38197", "85321", "76057"]:
    to_label_df = analytics.surgery.df[analytics.surgery.df["start_dt"].notna()]
    labelled_df = analytics.usage.label_events_with_pref_item_fill_qty(item_id, analytics.case_cart.df, to_label_df)

    labelled_df["start_date"] = labelled_df["start_dt"].apply(lambda x: x.date())
    surgeries = set(labelled_df["fill_qty"])
    if 0.0 in surgeries:
        surgeries.remove(0.0)

    for surgery in surgeries:
        label_filter = {"dim": "fill_qty",
                        "op": "eq",
                        "val": surgery}
        urgent_filter = {"dim": "urgent_elective",
                         "op": "eq",
                         "val": "Urgent"}
        elective_filter = {"dim": "urgent_elective",
                           "op": "eq",
                           "val": "Elective"}
        start = min(labelled_df[labelled_df["fill_qty"] == surgery]["start_date"])
        end = max(labelled_df[labelled_df["fill_qty"] == surgery]["start_date"])


        urgent_surgery_demand_dist = SurgeriesPerDayDistribution().get_data(labelled_df,
                                                                            filters=[label_filter,
                                                                                     urgent_filter],
                                                                            args={"start": start,
                                                                                  "end": end}
                                                                            )

        elective_surgery_demand_dist = SurgeriesPerDayDistribution().get_data(labelled_df,
                                                                              filters=[label_filter,
                                                                                       elective_filter],
                                                                              args={"start": start,
                                                                                    "end": end}
                                                                              )

        corr = np.corrcoef(urgent_surgery_demand_dist, elective_surgery_demand_dist)
        print("item id:{0}, surgery label:{1}".format(item_id, str(surgery)))
        print(corr)
