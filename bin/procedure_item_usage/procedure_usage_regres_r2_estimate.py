import pandas as pd
import pickle
import numpy as np
import statsmodels.api as sm

from scm_analytics import ScmAnalytics, config
from itertools import combinations
from pandas import Series
from statsmodels.api import families
from os import path, listdir

def run(case_service="Cardiac Surgery", item_id="38242", occurrence_thres=0):
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    usage_df = analytics.usage.df
    usage_df = usage_df[usage_df["item_id"] == item_id]
    usage_df = usage_df[usage_df["case_service"] == case_service]
    usage_df = usage_df.drop_duplicates(subset=["event_id"])

    surgery_df = analytics.surgery.df
    surgery_df = surgery_df[surgery_df["case_service"] == case_service]
    surgery_df = surgery_df[surgery_df["event_id"].isin(set(analytics.usage.df["event_id"]))]
    surgery_df = surgery_df.drop_duplicates(subset=["event_id"])

    surgery_df["procedures_count"] = surgery_df["procedures"].apply(lambda v: len(v))

    procedure_df = pd.concat([Series(row['event_id'], row['procedures']) for _, row in surgery_df.iterrows()],
                                 ).reset_index().rename(columns={"index": "procedure",
                                                                 0: "event_id"})
    procedure_df["flag"] = 1
    surg_regres_df = procedure_df\
        .pivot(index="event_id", columns="procedure", values="flag")\
        .fillna(0)\
        .reset_index()

    surg_regres_df = surg_regres_df.join(
        usage_df[usage_df["item_id"] == item_id][["event_id", "used_qty"]].set_index("event_id"),
        on="event_id",
        how="left",
        rsuffix="usage").fillna(0)


    all_procedures = set(procedure_df["procedure"])

    procedures = sorted(list(all_procedures))

    surg_regres_df["procedure_vector"] = surg_regres_df[[p for p in procedures]].values.tolist()
    surg_regres_df["procedure_vector"] = surg_regres_df["procedure_vector"].apply(lambda x: tuple(x))

    r2_df = surg_regres_df.groupby("procedure_vector")["used_qty"].apply(list)
    r2_df = surg_regres_df.groupby("procedure_vector").agg({"used_qty": list}).reset_index()

    r2_df["used_average"] = r2_df["used_qty"].apply(lambda x: np.mean(x))
    r2_df["occurrences"] = r2_df["used_qty"].apply(lambda x: len(x))

    r2_df = r2_df[r2_df["occurrences"] > occurrence_thres]
    r2_df["variance"] = r2_df["used_qty"].apply(lambda x: np.var(x))

    ss_tot = len(surg_regres_df) * np.var(surg_regres_df["used_qty"])
    ss_res_bound = sum(r2_df["occurrences"] * r2_df["variance"])
    r2_upper_bound = 1 - ss_res_bound/ss_tot
    print(r2_upper_bound)
    return


if __name__ == "__main__":
    ids = [79175,
           38160,
           38206,
           36556,
           36038,
           3070,
           1308,
           36555,
           38242,
           1122,
           3181,
           47320,
           38197,
           56931,
           44568,
           36558,
           21920,
           133221,
           82099,
           84364
           ]

    for id in ids:
        run(item_id=str(id))