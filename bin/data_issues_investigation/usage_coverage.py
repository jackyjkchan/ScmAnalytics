from scm_analytics import ScmAnalytics, config
from os import path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math

analytics = ScmAnalytics.ScmAnalytics(config.LHS())

usage = analytics.usage.df
usage = usage[usage["start_dt"].notna()]
surgeries = analytics.surgery.df

s = min(usage["start_dt"])
e = max(usage["start_dt"])

surgeries = surgeries[surgeries["start_dt"] >= s]
surgeries = surgeries[surgeries["start_dt"] <= e]


surgeries["year_week"] = surgeries["start_dt"].\
            apply(lambda x: "{0}-{1}".format(str(x.year-1 if (x.month == 1 and x.week == 52) else x.year),
                                             str(x.week) if x.week > 9 else "0" + str(x.week)))
usage["year_week"] = usage["start_dt"].\
            apply(lambda x: "{0}-{1}".format(str(x.year-1 if (x.month == 1 and x.week == 52) else x.year),
                                             str(x.week) if x.week > 9 else "0" + str(x.week)))

usage["has_usage"] = 1
has_usage_lkup = usage.groupby(["event_id"]).agg({'has_usage': "min"}).reset_index()


# filter if wanted
week_1 = min(usage["year_week"].apply(
        lambda x: int(x.split("-")[0])*52 + int(x.split("-")[1])))

for case_service in set(surgeries["case_service"]).union({None}):
    surgery_filter = {"dim": "case_service",
                      "op": "eq",
                      "val": case_service}
    if case_service:
        filtered_surgeries = analytics.process_filters(surgeries, [surgery_filter])
    else:
        filtered_surgeries = surgeries
    print(case_service, len(filtered_surgeries))

    filtered_surgeries = filtered_surgeries.join(has_usage_lkup[["event_id", "has_usage"]].set_index("event_id"),
                               on="event_id",
                               how="left",
                               rsuffix="usage")
    filtered_surgeries["has_usage"] = filtered_surgeries["has_usage"].apply(lambda x: 0 if math.isnan(x) else x)

    has_usage_ratio = filtered_surgeries.groupby(["year_week"]).agg({
        "has_usage": "sum",
        "event_id": "count"
    }).reset_index()

    has_usage_ratio["has_usage_ratio"] = has_usage_ratio["has_usage"] / has_usage_ratio["event_id"]
    has_usage_ratio["week_number"] = has_usage_ratio["year_week"].apply(
        lambda x: int(x.split("-")[0])*52 + int(x.split("-")[1]))
    has_usage_ratio["week_number"] = has_usage_ratio["week_number"] - week_1

    label = case_service if case_service else "All Surgeries"
    label = label + "({0})".format(str(len(filtered_surgeries)))
    plt.figure(figsize=(12, 6))
    plt.plot(has_usage_ratio["week_number"], has_usage_ratio["has_usage_ratio"], label=label)
    title = "Ratio of Surgeries with Usage Data Per Week Starting from First Instance of Usage Data"
    title = title + "[{0}]".format(label.replace("/"," "))
    plt.title(title)
    plt.ylabel("Ratio of Surgeries with Usage data")
    plt.xlabel("Week # starting from first week of OrangeBag project")
    plt.legend()
    plt.savefig(path.join(path.join("results"), title + ".svg"),
                format='svg',
                orientation='landscape',
                papertype='letter')
    #plt.show()

