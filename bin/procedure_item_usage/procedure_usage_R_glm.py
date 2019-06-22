import pandas as pd
import numpy as np
import subprocess
import time
import os

from scm_analytics import ScmAnalytics, config
from itertools import combinations
from pandas import Series
from pprint import pprint


def compute_rsquares(y, fit):
    y_bar = np.mean(y)
    ss_tot = sum((y_bar - y)**2)
    ss_res = sum((fit - y)**2)

    r2 = 1 - ss_res/ss_tot
    return r2


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.mode.chained_assignment = None


def run(case_service="Cardiac Surgery",
        item_id="38242",
        add_interactions=True,
        add_intercept=False,
        add_other_flag=True,
        add_procedures_count=False,
        pre_screen=True,
        p_thres=0.05,
        occurrence_thres=0,
        primary_model="gaussian",
        secondary_model="hurdlepoisson"
        ):

    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    usage_df = analytics.usage.df
    usage_df = usage_df[usage_df["item_id"] == item_id]
    usage_df = usage_df[usage_df["case_service"] == case_service]
    usage_df = usage_df.drop_duplicates(subset=["event_id"])

    surgery_df = analytics.surgery.df
    surgery_df = surgery_df[surgery_df["case_service"] == case_service]
    surgery_df = surgery_df[surgery_df["event_id"].isin(set(analytics.usage.df["event_id"]))]
    surgery_df = surgery_df.drop_duplicates(subset=["event_id"])
    surgery_df["procedures"] = surgery_df["procedures"].apply(lambda x: set(e.replace(" ", "_") for e in x))

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

    surg_regres_df = surg_regres_df.join(
        surgery_df[["event_id", "procedures_count"]].set_index("event_id"),
        on="event_id",
        how="left",
        rsuffix="cnt").fillna(0)

    regression_summary = procedure_df.groupby(["procedure"])\
                                     .agg({"event_id": "nunique"})\
                                     .reset_index()\
                                     .rename(columns={"event_id": "occurrences"})

    all_procedures = set(regression_summary["procedure"])
    procedures = sorted(list(set(regression_summary[regression_summary["occurrences"] > occurrence_thres]["procedure"])))

    if pre_screen:
        df = surgery_df.join(usage_df[["event_id", "used_qty"]].set_index("event_id"),
                             on="event_id",
                             how="left",
                             rsuffix="usage")
        screened_procedures = set.union(*df[df["used_qty"]>0]["procedures"])
        procedures = list(filter(lambda x: x in screened_procedures, procedures))
        surg_regres_df["pre_screen"] = surg_regres_df[procedures].values.tolist()
        surg_regres_df["pre_screen"] = surg_regres_df["pre_screen"].apply(lambda x: any(x))
        surg_regres_df = surg_regres_df[surg_regres_df["pre_screen"]].reset_index()
    regression_summary = regression_summary[regression_summary["procedure"].isin(procedures)]

    # add interaction effects
    if add_interactions:
        fmt = "xX{0}.{1}Xx"
        interactions = {fmt.format(p1, p2): [p1, p2] for p1, p2 in combinations(procedures, 2)}
        for p1, p2 in combinations(procedures, 2):
            comb_col = (surg_regres_df[p2].astype(bool) & surg_regres_df[p1].astype(bool)).astype(float)
            if sum(comb_col) > occurrence_thres:
                surg_regres_df[fmt.format(p1, p2)] = comb_col
                procedures.append(fmt.format(p1, p2))
                regression_summary = regression_summary.append({"procedure": fmt.format(p1, p2),
                                                                "occurrences": sum(comb_col)},
                                                               ignore_index=True)
    surg_regres_df["procedure_vector"] = surg_regres_df[procedures].values.tolist()

    count = 0
    while True:
        export_df = surg_regres_df[procedures] if procedures else pd.DataFrame()
        export_df["y"] = surg_regres_df["used_qty"]

        if add_intercept:
            export_df["CONSTANT"] = 1
        other_added = False
        if add_other_flag:
            other = np.array(list([0] if any(e) else [1] for e in export_df[procedures].values.tolist()))
            if sum(other) > occurrence_thres:
                export_df["OTHER"] = other
                other_added = True
            else:
                other_added = False

        if add_procedures_count:
            export_df["procedures_count"] = surg_regres_df["procedures_count"]

        export_df.to_csv("R_Dump/data.csv", index=False)
        time.sleep(0.2)
        process = subprocess.Popen(["Rscript", "--vanilla", "R_Dump/run_glm.r", "data.csv", "R_Dump", primary_model],
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.wait()
        stderr = process.stderr.read()
        print(stderr)
        if not (os.path.isfile("R_Dump/fit.csv") and os.path.isfile("R_Dump/r_summary.csv")):
            print("ERROR001")
            return None, None, None

        results_df = pd.read_csv("R_Dump/r_summary.csv", index_col=0)
        fit = pd.read_csv("R_Dump/fit.csv")["fit"]
        y = export_df["y"]
        os.remove("R_Dump/fit.csv")
        os.remove("R_Dump/r_summary.csv")
        p_col = results_df.columns[-1]
        pvalues = list(regression_summary.join(results_df,
                                on="procedure",
                                how="left",
                                rsuffix="R")[p_col].fillna(100))


        count += 1
        coeff_names = procedures.copy()

        if add_intercept:
            coeff_names.append("CONSTANT")
        if other_added:
            coeff_names.append("OTHER")
        if add_procedures_count:
            coeff_names.append("COUNT")
        extra_rows = sum(int(f) for f in [other_added, add_intercept, add_procedures_count])

        end = len(pvalues) - extra_rows
        p_values = pvalues[0:end]

        if all(p_val <= p_thres for p_val in p_values):
            break
        else:
            procedures = list(filter(
                lambda v: {procedures[i]: pvalues[i] for i in range(len(pvalues))}[v] <= p_thres, procedures))
            surg_regres_df["procedure_vector"] = surg_regres_df[[p for p in procedures]].values.tolist()
            regression_summary = regression_summary[regression_summary["procedure"].isin(procedures)]

    r2_original = None
    r2s = [compute_rsquares(y, fit)]
    if secondary_model:
        if not isinstance(secondary_model, list):
            secondary_model = [secondary_model]

        for model in secondary_model:
            export_df.to_csv("R_Dump/data.csv", index=False)
            time.sleep(0.2)
            process = subprocess.Popen(["Rscript", "--vanilla", "R_Dump/run_glm.r", "data.csv", "R_Dump", model],
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            process.wait()
            stderr = process.stderr.read()
            print(stderr)
            if not (os.path.isfile("R_Dump/fit.csv") and os.path.isfile("R_Dump/r_summary.csv")):
                print("ERROR002")
                r2s.append(None)
                continue
            results_df = pd.read_csv("R_Dump/r_summary.csv", index_col=0)
            fit = pd.read_csv("R_Dump/fit.csv")["fit"]
            #os.remove("R_Dump/fit.csv")
            #os.remove("R_Dump/r_summary.csv")
            p_col = results_df.columns[-1]
            pvalues = list(regression_summary.join(results_df,
                                                   on="procedure",
                                                   how="left",
                                                   rsuffix="R")[p_col].fillna(1))
            r2s.append(compute_rsquares(y, fit))


    remaining_procedures = all_procedures.intersection(procedures)
    regression_summary = regression_summary[regression_summary["procedure"].isin(procedures)]

    regression_summary = regression_summary.join(results_df,
                                                 on="procedure",
                                                 how="left",
                                                 rsuffix="R")

    if add_intercept:
        procedures.append("CONSTANT")
        regression_summary = regression_summary.append({"procedure": "CONSTANT",
                                                        "occurrences": -1},
                                                       ignore_index=True)
    if other_added:
        procedures.append("OTHER")
        cnt = sum(export_df["OTHER"])
        regression_summary = regression_summary.append({"procedure": "OTHER",
                                                        "occurrences": cnt},
                                                       ignore_index=True)
    if add_procedures_count:
        procedures.append("COUNT")
        cnt = "NA"
        regression_summary = regression_summary.append({"procedure": "OTHER",
                                                        "occurrences": cnt},
                                                         ignore_index=True)

    if add_interactions:
        remaining_interactions = sorted(list(set(i for i in interactions).intersection(procedures)))
        interaction_status = list(int(interactions[e][0] in procedures) + int(interactions[e][1] in procedures)
                                  for e in remaining_interactions
                                  )
        regression_summary["interaction status"] = ["NA"] * len(remaining_procedures) + \
                                                   interaction_status + \
                                                   ["NA"]*extra_rows
    else:
        remaining_interactions = []

    r2 = compute_rsquares(y, fit)

    #print(regression_summary)
    #print(r2s)

    #print("Procedures Kept:{0:d}/{1:d}".format(len(remaining_procedures), len(all_procedures)))
    #if add_interactions:
    #    print("Interactions kept: {0:d}/{1:d}".format(len(remaining_interactions), len(interactions)))
    #print(item_id, r2, len(remaining_procedures), len(remaining_interactions))

    return r2s, len(remaining_procedures), len(remaining_interactions)


if __name__ == "__main__":
    print(run(p_thres=0.05,
              occurrence_thres=10,
              add_intercept=False,
              add_procedures_count=False,
              add_interactions=True,
              add_other_flag=True,
              primary_model="gaussian",
              pre_screen=True,
              secondary_model=["poisson"],
              item_id=str(38242)))


if __name__ == "":

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
           84364]

    thres_values = [1, 0.5, 0.25, 0.2, 0.15, 0.1, 0.05, 0.01]
    df = pd.DataFrame(columns=["item_id",
                               'pThres',
                               'occThres',
                               'n_procedures',
                               'n_interactions',
                               'gaussian',
                               'poisson',
                               'nb',
                               "hurdlepoisson",
                               "hurdlenegbin"])
    models = ["poisson", "nb", "hurdlepoisson", "hurdlenegbin"]
    all_models = ["gaussian"] + models
    for id in ids:
        for add in [True, False]:
            for occThres in [0, 2, 5, 10]:
                for pthres in thres_values:
                    row = {"item_id": str(id),
                           "pThres": pthres,
                           "occThres": occThres}
                    r2s, n_procedures, n_interactions = run(p_thres=pthres,
                                                           occurrence_thres=occThres,
                                                           add_interactions=add,
                                                           primary_model="gaussian",
                                                           secondary_model=models,
                                                           item_id=str(id))
                    row["n_procedures"] = n_procedures
                    row["n_interactions"] = n_interactions
                    for i in range(len(all_models)):
                        row[all_models[i]] = r2s[i]
                    df = df.append(row, ignore_index=True)
                    df = df.fillna("Failed")

                    print(df)
                    df.to_csv("usage_regression_r_glm.csv", index=False)
