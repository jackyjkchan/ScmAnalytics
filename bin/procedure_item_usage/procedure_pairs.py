import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from scm_analytics import ScmAnalytics, config
from pandas import Series

# looks for procedures that always appear together. These will need to be combined for regression.

analytics = ScmAnalytics.ScmAnalytics(config.LHS())
usage_events = set(analytics.usage.df["event_id"])
surgery_df = analytics.surgery.df[analytics.surgery.df["scheduled_procedures"].notna()]
surgery_df["procedures_set"] = surgery_df["scheduled_procedures"].apply(lambda x: set(p.strip().lower()
                                                                                      for p in x.split(",")
                                                                                      ))
surgery_df["procedures_count"] = surgery_df["scheduled_procedures"].apply(lambda x: len(x))
surgery_df = surgery_df[surgery_df["event_id"].isin(usage_events)]

procedure_df = pd.concat([Series(row['event_id'], row['procedures_set']) for _, row in surgery_df.iterrows()],
                         ).reset_index().rename(columns={"index": "procedure",
                                                         0: "event_id"})
procedure_df = procedure_df.join(surgery_df[["event_id", "case_service"]].set_index("event_id"),
                  on="event_id",
                  how="left",
                  rsuffix="case")

case_serv_pairs = {}


for case_service in ["Cardiac Surgery"]:#set(procedure_df["case_service"]):
    print(case_service)
    procedure_pairs = set()
    df = procedure_df[procedure_df["case_service"] == case_service]
    procedures = list(set(df["procedure"]))
    for i in range(len(procedures)-1):
        print("{0}/{1}".format(str(i), str(len(procedures))))
        for j in range(i+1, len(procedures)):
            p1 = procedures[i]
            p2 = procedures[j]
            events1 = set(df[df["procedure"] == p1]["event_id"])
            events2 = set(df[df["procedure"] == p2]["event_id"])
            if events1 == events2:
                procedure_pairs.add((p1, p2))
    case_serv_pairs[case_service] = procedure_pairs
print(case_serv_pairs)


for cs in case_serv_pairs:
    new_sets = []
    for t in case_serv_pairs[cs]:
        flag = True
        t = set(t)
        for j in new_sets:
            if t.intersection(j):
                j.update(t)
                flag = False
                break
        if flag:
            new_sets.append(t)
    case_serv_pairs[cs] = new_sets

for cs in case_serv_pairs:
    reduction = sum(len(x) for x in case_serv_pairs[cs]) - len(case_serv_pairs[cs])
    print("\t".join([cs+": {0}".format(str(reduction))]+list(str(x) for x in case_serv_pairs[cs])))
