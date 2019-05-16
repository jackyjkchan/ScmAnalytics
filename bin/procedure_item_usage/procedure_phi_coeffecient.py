import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import scipy

from scm_analytics import ScmAnalytics, config
from pandas import Series
from pprint import pprint

case_service = "Cardiac Surgery"
item_id = "38242"
thres = 0.05


def phi_coeff(x1, x2):
    n11 = sum(1 if (x1[i] == 1 and x2[i] == 1) else 0 for i in range(len(x1)))
    n01 = sum(1 if (x1[i] == 0 and x2[i] == 1) else 0 for i in range(len(x1)))
    n10 = sum(1 if (x1[i] == 1 and x2[i] == 0) else 0 for i in range(len(x1)))
    n00 = sum(1 if (x1[i] == 0 and x2[i] == 0) else 0 for i in range(len(x1)))
    n_1 = n01+n11
    n_0 = n00+n10
    n1_ = n10+n11
    n0_ = n01+n00
    return (n11*n00-n10*n01)/(np.sqrt(n_1*n_0*n1_*n0_)) if all([n_1, n_0, n1_, n0_]) else None


analytics = ScmAnalytics.ScmAnalytics(config.LHS())
case_services = set(analytics.surgery.df["case_service"])

for case_service in ["General Surgery", "Plastic Surgery"]:
    print(case_service)
    usage_df = analytics.usage.df
    usage_df = usage_df[usage_df["item_id"] == item_id]
    usage_df = usage_df[usage_df["case_service"] == case_service]
    usage_df = usage_df.drop_duplicates(subset=["event_id"])

    surgery_df = analytics.surgery.df
    surgery_df = surgery_df[surgery_df["case_service"] == case_service]
    surgery_df = surgery_df[surgery_df["scheduled_procedures"].notna()]
    surgery_df = surgery_df[surgery_df["event_id"].isin(set(analytics.usage.df["event_id"]))]
    surgery_df = surgery_df.drop_duplicates(subset=["event_id"])
    surgery_df["procedures_set"] = surgery_df["scheduled_procedures"].apply(lambda val:
                                                                            set([p.strip().lower()for p in val.split(",")])
                                                                            )
    surgery_df["procedures_count"] = surgery_df["procedures_set"].apply(lambda v: len(v))
    procedure_df = pd.concat([Series(row['event_id'], row['procedures_set']) for _, row in surgery_df.iterrows()],
                             ).reset_index().rename(columns={"index": "procedure",
                                                             0: "event_id"})
    procedure_df["flag"] = 1
    surg_regres_df = procedure_df\
        .pivot(index="event_id", columns="procedure", values="flag")\
        .fillna(0)\
        .reset_index()

    # surg_regres_df = surg_regres_df.join(
    #     usage_df[usage_df["item_id"] == item_id][["event_id", "used_qty"]].set_index("event_id"),
    #     on="event_id",
    #     how="left",
    #     rsuffix="usage").fillna(0)

    procedures = sorted(list(set(procedure_df["procedure"])))
    surg_regres_df["procedure_vector"] = surg_regres_df[[p for p in procedures]].values.tolist()

    #y = surg_regres_df["used_qty"]
    x = np.array(list(surg_regres_df["procedure_vector"]))

    coeffs = []
    for i in range(len(procedures)):
        print("{0}/{1}".format(str(i), str(len(procedures))))
        coeff = []
        x1 = list(r[i] for r in x)
        for j in range(len(procedures)):
            x2 = list(r[j] for r in x)
            coeff.append(phi_coeff(x1, x2))
        coeffs.append(coeff)


    with open("{0}_item_id_{1}_procedure_phi_coeff.csv".format(case_service.replace(" ", "_"), item_id), "w") as f:
        f.write("procedures,")
        f.write(",".join(p for p in procedures))
        f.write("\n")
        for i in range(len(procedures)):
            p = procedures[i]
            f.write("{0},".format(p))
            f.write(",".join("{0:1.3f}".format(x) for x in coeffs[i]))
            f.write("\n")
