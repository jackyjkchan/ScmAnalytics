import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from scm_analytics import ScmAnalytics, config
from pandas import Series

analytics = ScmAnalytics.ScmAnalytics(config.LHS())
usage_events = set(analytics.usage.df["event_id"])
surgery_df = analytics.surgery.df[analytics.surgery.df["scheduled_procedures"].notna()]
surgery_df["procedures_set"] = surgery_df["scheduled_procedures"].apply(lambda x: set(p.strip().lower()
                                                                                      for p in x.split(",")
                                                                                      ))
surgery_df["procedures_count"] = surgery_df["procedures_set"].apply(lambda x: len(x))
surgery_df = surgery_df[surgery_df["event_id"].isin(usage_events)]

step = 1
print(min(surgery_df["procedures_count"]))
print(max(surgery_df["procedures_count"]))
bins = range(0, max(surgery_df["procedures_count"])+step, step)
fig_size = (10, 4)
fig, ax = plt.subplots(figsize=fig_size)
plt.hist(surgery_df["procedures_count"], bins=bins, rwidth=0.96, alpha=0.5)
plt.title("Distribution of Procedures Per Surgery (During OrangeBag Project)")
plt.xlabel("Procedures Per Surgery")
plt.ylabel("Frequency (Count Of Surgeries)")
#plt.show()
plt.savefig("procedures_per_surgery.png",
            format='png',
            orientation='landscape',
            papertype='letter')
plt.close()

for case_service in set(surgery_df["case_service"]):
    label_str = case_service.replace("/", " ")
    df = surgery_df[surgery_df["case_service"] == case_service]
    step = 1
    print(min(df["procedures_count"]))
    print(max(df["procedures_count"]))
    bins = range(0, max(df["procedures_count"]) + step, step)
    fig_size = (10, 4)
    fig, ax = plt.subplots(figsize=fig_size)
    plt.hist(df["procedures_count"], bins=bins, rwidth=0.96, alpha=0.5)
    plt.title("Distribution of Procedures Per '{0}' Surgery (During OrangeBag Project)".format(label_str))
    plt.xlabel("Procedures Per Surgery")
    plt.ylabel("Frequency (Count Of Surgeries)")
    plt.savefig("procedures_per_surgery_{0}.svg".format(label_str),
                format='svg',
                orientation='landscape',
                papertype='letter')
    plt.close()
exit(0)
procedure_df = pd.concat([Series(row['event_id'], row['procedures_set']) for _, row in surgery_df.iterrows()],
                         ).reset_index().rename(columns={"index": "procedure",
                                                         0: "event_id"})
procedure_df = procedure_df.join(surgery_df[["event_id", "case_service"]].set_index("event_id"),
                  on="event_id",
                  how="left",
                  rsuffix="case")


usage_procedures = procedure_df[procedure_df["event_id"].isin(usage_events)]
summary_df = usage_procedures.groupby(["procedure"]).agg({"event_id": "nunique"}).reset_index()
step = 10
overflow = 100
data = list(summary_df["event_id"])
bins = range(0, max(data)+step, step)
fig_size = (10, 4)

bins = range(0, overflow + step, step)
data = np.clip(data, 0, overflow)

xlabels = [str(x) for x in bins[0:-1]]
xlabels[-1] += "+"

fig, ax = plt.subplots(figsize=fig_size)
plt.hist(data, bins=bins, rwidth=0.96, alpha=0.5)
plt.title("Distribution of Procedures Occurrences (During OrangeBag Project)")
plt.xlabel("Times a Procedure was Scheduled")
plt.ylabel("Frequency (Procedure Count)")
plt.xticks(step * np.arange(len(xlabels)), xlabels)
#plt.show()
plt.close()

for case_service in set(surgery_df["case_service"]):
    label_str = case_service.replace("/", " ")
    df = procedure_df[procedure_df["case_service"] == case_service]
    summary_df = df.groupby(["procedure"]).agg({"event_id": "nunique"}).reset_index()
    step = 10
    overflow = 100
    data = list(summary_df["event_id"])
    bins = range(0, max(data) + step, step)
    fig_size = (10, 4)

    bins = range(0, overflow + step, step)
    data = np.clip(data, 0, overflow)

    xlabels = [str(x) for x in bins[0:-1]]
    xlabels[-1] += "+"

    fig, ax = plt.subplots(figsize=fig_size)
    plt.hist(data, bins=bins, rwidth=0.96, alpha=0.5)
    plt.title("Distribution of Procedures Occurrences '{0}' (During OrangeBag Project)".format(label_str))
    plt.xlabel("Times a Procedure was Scheduled")
    plt.ylabel("Frequency (Procedure Count)")
    plt.xticks(step * np.arange(len(xlabels)), xlabels)
    #plt.show()
    plt.savefig("procedures_occurences_{0}.svg".format(label_str),
                format='svg',
                orientation='landscape',
                papertype='letter')
    plt.close()




