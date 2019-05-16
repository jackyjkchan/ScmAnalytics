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
surgery_df["procedures_count"] = surgery_df["scheduled_procedures"].apply(lambda x: len(x))
surgery_df = surgery_df[surgery_df["event_id"].isin(usage_events)]

procedure_df = pd.concat([Series(row['event_id'], row['procedures_set']) for _, row in surgery_df.iterrows()],
                         ).reset_index().rename(columns={"index": "procedure",
                                                         0: "event_id"})
procedure_df = procedure_df.join(surgery_df[["event_id", "case_service"]].set_index("event_id"),
                  on="event_id",
                  how="left",
                  rsuffix="case")

summary_df = procedure_df.groupby(["case_service"]).agg({"event_id": "nunique",
                                                         "procedure": "nunique"}).reset_index()
summary_df["surgery_procedure_ratio"] = summary_df["event_id"] / summary_df["procedure"]
print(summary_df)
summary_df.rename(columns={"event_id": "surgery_nunique",
                           "procedure": "procedures_nunique"})
summary_df.to_csv("surgery_procedure_ratio.csv")