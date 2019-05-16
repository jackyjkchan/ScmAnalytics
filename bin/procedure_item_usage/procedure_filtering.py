import pandas as pd

from scm_analytics import ScmAnalytics, config
from pandas import Series

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

procedures = set(procedure_df["procedure"])
usage_procedures = procedure_df[procedure_df["event_id"].isin(usage_events)]
summary_df = usage_procedures.groupby(["procedure"]).agg({"event_id": "nunique"}).reset_index()
summary_df = summary_df.sort_values(["event_id"])
procedures_to_remove = list(summary_df["procedure"])

must_keep_procedures = set()
for procedures in surgery_df[surgery_df["procedures_count"] == 1]["procedures_set"]:
    must_keep_procedures.update(procedures)

i = 1
for procedure in procedures_to_remove:
    print(i, "/", len(procedures_to_remove))
    if procedure not in must_keep_procedures:
        surgery_df["procedures_set"] = surgery_df["procedures_set"].apply(lambda x: x - set([procedure]))
        surgery_df["procedures_count"] = surgery_df["procedures_set"].apply(lambda x: len(x))
        for procedures in surgery_df[surgery_df["procedures_count"] == 1]["procedures_set"]:
            must_keep_procedures.update(procedures)
    i += 1
