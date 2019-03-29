from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.SurgeryMetrics import SurgeriesPerDayDistribution
import matplotlib.pyplot as plt

item_ids = ["38197", "85321", "76057"]
analytics = ScmAnalytics.ScmAnalytics(config.LHS())
for item_id in ["38197", "85321", "76057"]:
    to_label_df = analytics.surgery.df[analytics.surgery.df["start_dt"].notna()]
    labaled_df = analytics.usage.label_events_with_pref_item_fill_qty(item_id, analytics.case_cart.df, to_label_df)
    labaled_df["start_date"] = labaled_df["start_dt"].apply(lambda x: x.date())
    surgeries = set(labaled_df["fill_qty"])
    if 0.0 in surgeries:
        surgeries.remove(0.0)

    for surgery in surgeries:
        print(surgery)
        label_filter = {"dim": "fill_qty",
                        "op": "eq",
                        "val": surgery}
        urgent_filter = {"dim": "urgent_elective",
                         "op": "eq",
                         "val": "Urgent"}
        elective_filter = {"dim": "urgent_elective",
                           "op": "eq",
                           "val": "Elective"}
        start = min(labaled_df[labaled_df["fill_qty"] == surgery]["start_date"])
        end = max(labaled_df[labaled_df["fill_qty"] == surgery]["start_date"])


        urgent_surgery_demand_dist = SurgeriesPerDayDistribution().get_data(labaled_df,
                                                                            filters=[label_filter,
                                                                                     urgent_filter],
                                                                            args={"start": start,
                                                                                  "end": end}
                                                                            )

        elective_surgery_demand_dist = SurgeriesPerDayDistribution().get_data(labaled_df,
                                                                              filters=[label_filter,
                                                                                       elective_filter],
                                                                              args={"start": start,
                                                                                    "end": end}
                                                                              )
        xy = list(zip(urgent_surgery_demand_dist, elective_surgery_demand_dist))
        s = [xy.count(e) for e in xy]
        plt.scatter(elective_surgery_demand_dist,
                 urgent_surgery_demand_dist,
                 s = s,
                 label="surg_label:{0}".format(str(surgery)))

        title = "Plot of Urgent Vs Elective Surgeries in a Day item={0} label={1}".format(item_id, str(surgery))
        plt.title("Correlation Plot- Scatter plot of Urgent Vs Elective Surgeries in a Day")
        plt.xlabel("Number of Elective Surgeries in a Day")
        plt.ylabel("Number of Urgent Surgeries in a Day")
        plt.legend()
        plt.savefig(title + ".svg",
                    format='svg',
                    orientation='landscape',
                    papertype='letter')
        plt.close()
