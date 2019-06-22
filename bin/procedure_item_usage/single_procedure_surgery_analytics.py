import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import scipy
import math
import os

from scm_analytics import ScmAnalytics, config
from scipy import stats, optimize, interpolate
from pandas import Series

thres = 15

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

case_services = ["Cardiac Surgery", "Dental Surgery", "Obstetrics/Gynecology"]
case_service_item_ids = {
    "Cardiac Surgery": ["79175", "38242", "47320"],
    "Dental Surgery": ["98473", "115873", "115877"],
    "Obstetrics/Gynecology": ["100135", "44165", "36535"]
}

analytics = ScmAnalytics.ScmAnalytics(config.LHS())
analytics.analyze_item_usage_by_case_service()

for case_service in case_services:
    sub_dir = case_service.replace("/", " ")
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)

    items = analytics.item_catalog_df[
                (analytics.item_catalog_df[case_service] > 0.95) & (analytics.item_catalog_df['total_used_qty'] > 100)
            ].sort_values("total_used_qty", ascending=False)[0:10]["item_id"]

    surgery_df = analytics.surgery.df
    surgery_df = surgery_df[surgery_df["case_service"] == case_service]
    surgery_df = surgery_df[surgery_df["scheduled_procedures"].notna()]
    surgery_df = surgery_df[surgery_df["event_id"].isin(set(analytics.usage.df["event_id"]))]
    surgery_df = surgery_df.drop_duplicates(subset=["event_id"])
    surgery_df["procedures_set"] = surgery_df["scheduled_procedures"].apply(lambda val:
                                                                            set([p.strip().lower() for p in
                                                                                 val.split(",")])
                                                                            )
    surgery_df["procedures_count"] = surgery_df["procedures_set"].apply(lambda v: len(v))
    procedure_df = pd.concat([Series(row['event_id'], row['procedures_set']) for _, row in surgery_df.iterrows()],
                             ).reset_index().rename(columns={"index": "procedure",
                                                             0: "event_id"})
    procedure_df = procedure_df.join(surgery_df[["event_id", "procedures_count"]].set_index("event_id"),
                                     on="event_id",
                                     how="left",
                                     rsuffix="count")
    procedure_summary = procedure_df.groupby(["procedure", "procedures_count"]) \
        .agg({"event_id": "nunique"}) \
        .reset_index() \
        .rename(columns={"event_id": "occurrences"})

    procedure_summary = procedure_summary \
        .pivot(index="procedure", columns="procedures_count", values="occurrences") \
        .fillna(0) \
        .reset_index()
    procedure_summary.to_csv(os.path.join(sub_dir, "procedure_occurences.csv"))

    procedure_item_usage_summary = procedure_summary[procedure_summary[1] > thres][["procedure"]]

    for item_id in items:
        usage_df = analytics.usage.df
        usage_df = usage_df[usage_df["item_id"] == item_id]
        usage_df = usage_df[usage_df["case_service"] == case_service]
        usage_df = usage_df.drop_duplicates(subset=["event_id"])

        df = surgery_df.join(
            usage_df[usage_df["item_id"] == item_id][["event_id", "used_qty"]].set_index("event_id"),
            on="event_id",
            how="left",
            rsuffix="usage").fillna(0)
        mus = []
        vars = []
        for procedure in procedure_item_usage_summary["procedure"]:
            print(procedure)
            single_procedure_usages = df[df["procedures_set"] == set([procedure])]["used_qty"]
            mus.append(np.mean(single_procedure_usages))
            vars.append(np.var(single_procedure_usages, ddof=1))
            bins = range(0, int(max(single_procedure_usages)+2), 1)
            fig_size = (10, 4)
            fig, ax = plt.subplots(figsize=fig_size)
            plt.hist(single_procedure_usages, bins=bins, rwidth=0.96, alpha=0.5)
            plt.xticks(bins)
            plt.title(
                "Distribution of Item Usage for Single Procedure Cases\n item_id:{0} procedure:{1}".format(item_id,
                                                                                                           procedure)
            )
            plt.xlabel("Used Qty Per Surgery")
            plt.ylabel("Frequency (Count Of Surgeries)")
            # plt.show()
            fn = "usages_per_surgery_single_procedure_case_{0}_{1}.png".format(item_id, procedure.replace("/", " "))

            plt.savefig(os.path.join(sub_dir, fn),
                        format='png',
                        orientation='landscape',
                        papertype='letter')
            plt.close()
        procedure_item_usage_summary["{0}_mean".format(item_id)] = mus
        procedure_item_usage_summary["{0}_var".format(item_id)] = vars

    procedure_item_usage_summary.to_csv(os.path.join(sub_dir, "single_procedure_item_usages_summary.csv"))
