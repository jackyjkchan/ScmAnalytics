import pandas as pd
import pickle
import numpy as np
import statsmodels.api as sm

from scm_analytics import ScmAnalytics, config
from itertools import combinations
from pandas import Series
from statsmodels.api import families
from os import path, listdir


def compute_rsquares(x, y, ols_results):
    for i in range(len(y)):
        print(y[i], ols_results.fittedvalues[i])
    y_bar = np.mean(y)
    ss_tot = sum((y_bar - y)**2)
    ss_res = sum((ols_results.fittedvalues - y)**2)
    r2 = 1 - ss_res/ss_tot
    return r2


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def run(service="Cardiac Surgery",
        item="38242",
        add_interactions=True,
        add_intercept=False,
        add_other_flag=True,
        pre_screen=True,
        pthres=0.05,
        occ_thres=5,
        glm_model=families.Gaussian(),
        secondary_model=families.Poisson()):
    case_service = service
    item_id = item
    p_thres = pthres
    occurrence_thres = occ_thres

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

    regression_summary = procedure_df.groupby(["procedure"])\
                                     .agg({"event_id": "nunique"})\
                                     .reset_index()\
                                     .rename(columns={"event_id": "occurrences"})

    #print("Initial List of Procedures and Count of Occurences over {0:d} Surgery Samples".format(len(surg_regres_df)))
    #print(regression_summary.to_string(index=False))

    all_procedures = set(regression_summary["procedure"])
    procedures = sorted(list(set(regression_summary[regression_summary["occurrences"] > occurrence_thres]["procedure"])))

    if pre_screen:
        df = surgery_df.join(usage_df[["event_id", "used_qty"]].set_index("event_id"),
                             on="event_id",
                             how="left",
                             rsuffix="usage")
        screened_procedures = set.union(*df[df["used_qty"]>0]["procedures"])
        procedures = list(filter(lambda x: x in screened_procedures, procedures))


    # add interaction effects
    if add_interactions:
        interactions = {"_{0}*{1}_".format(p1, p2): [p1, p2] for p1, p2 in combinations(procedures, 2)}
        for p1, p2 in combinations(procedures, 2):
            comb_col = (surg_regres_df[p2].astype(bool) & surg_regres_df[p1].astype(bool)).astype(float)
            if sum(comb_col) > 5:
                surg_regres_df["_{0}*{1}_".format(p1, p2)] = comb_col
                procedures.append("_{0}*{1}_".format(p1, p2))
                regression_summary = regression_summary.append({"procedure": "_{0}*{1}_".format(p1, p2),
                                                                "occurrences": sum(comb_col)},
                                                               ignore_index=True)

    excluded_procedures = all_procedures - set(procedures)
    surg_regres_df["procedure_vector"] = surg_regres_df[[p for p in procedures]].values.tolist()

    count = 0
    while True:
        y = surg_regres_df["used_qty"]

        x = np.array(list(surg_regres_df["procedure_vector"]))
        if add_intercept:
            x = sm.add_constant(x)
        other_added = False
        if add_other_flag:
            other = np.array(list([0] if any(e) else [1] for e in x))
            if sum(other) > occurrence_thres:
                x = np.append(x, other, axis=1)
                other_added = True
            else:
                other_added = False
        # for line in x:
        #     print(" ".join(str(v) for v in line))
        # print(y)
        results = sm.GLM(y, x, family=glm_model).fit()
        count += 1
        coeff_names = procedures.copy()

        if add_intercept:
            coeff_names.append("CONSTANT")
        if other_added:
            coeff_names.append("OTHER")
        extra_rows = sum(int(f) for f in [other_added, add_intercept])

        end = len(results.pvalues) - extra_rows
        p_values = results.pvalues[0:end]

        if all(p_val <= p_thres for p_val in p_values):
            break
        else:
            procedures = list(filter(
                lambda v: {procedures[i]: p_values[i] for i in range(len(p_values))}[v] <= p_thres, procedures))
            surg_regres_df["procedure_vector"] = surg_regres_df[[p for p in procedures]].values.tolist()

    if secondary_model:
        results = sm.GLM(y, x, family=secondary_model).fit()

    remaining_procedures = all_procedures.intersection(procedures)
    regression_summary = regression_summary[regression_summary["procedure"].isin(procedures)]

    if add_intercept:
        procedures.append("CONSTANT")
        regression_summary = regression_summary.append({"procedure": "CONSTANT",
                                                        "occurrences": -1},
                                                       ignore_index=True)
    if other_added:
        procedures.append("OTHER")
        cnt = sum(v[-1] for v in x)
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

    regression_summary["coeff"] = list(results.params)
    regression_summary["pvalue"] = list(results.pvalues)

    r2 = compute_rsquares(x, y, results)

    print(regression_summary)
    #print(procedures)

    print("R2:", r2)
    #print("Procedures Kept:{0:d}/{1:d}".format(len(remaining_procedures), len(all_procedures)))
    #if add_interactions:
    #    print("Interactions kept: {0:d}/{1:d}".format(len(remaining_interactions), len(interactions)))
    #print(item_id, r2, len(remaining_procedures), len(remaining_interactions))

    results_cache = {
        "regression_summary": regression_summary,
        "R2": r2,
        "remaining_procedures": remaining_procedures,
        "all_procedures": all_procedures,
        "remaining_interactions": remaining_interactions if add_interactions else None,
        "args": (service, item, add_interactions, add_intercept, add_other_flag, pthres, occ_thres, glm_model)
    }

    fam_n = str(type(glm_model)).strip("'>").split(".")[-1]
    fn = "{0}_{1}_{2:0.3f}_{3:d}_{4}".format(service, item, pthres, occ_thres, fam_n)
    if add_interactions:
        fn += "_interactions"
    if add_intercept:
        fn += "_intercept"
    if add_other_flag:
        fn += "_other"
    fn += ".pickle"
    with open(path.join("glm_cache", fn), "wb") as f:
        pickle.dump(results_cache, f)
    return r2


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
    from pprint import pprint
    run()
    # for id in ids:
    #     run(item=str(id))

    # cached_results = listdir("glm_cache")
    # pprint(cached_results)
    # with open(path.join("glm_cache", cached_results[0]), "rb") as f:
    #     loaded_cache = pickle.load(f)
    #     print(loaded_cache["remaining_procedures"])
