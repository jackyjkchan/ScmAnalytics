import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import scipy
import math
import gurobipy

from scm_analytics import ScmAnalytics, config
from scipy import stats, optimize, interpolate
from pandas import Series
from pprint import pprint


def binom_fit(sample_mean, sample_var):
    n_list = list(range(math.ceil(sample_mean), math.ceil(sample_mean+5)))
    n = min(n_list, key=lambda x: (scipy.stats.binom.var(x, sample_mean/x) - sample_var)**2)
    return {i: scipy.stats.binom(n, sample_mean/n).pmf(i) for i in range(n+1)}

def binom_fit_params(discrete_dist):
    n = len(discrete_dist.keys())-1
    p = math.pow(discrete_dist[n], 1/n)
    return n, p

def discrete2_fit(sample_mean, sample_var):
    vals = [math.floor(sample_mean), math.ceil(sample_mean)]
    prob = [vals[0]+1-sample_mean]
    prob.append(1-prob[0])
    var = sum(prob[i]*vals[i]**2 for i in range(2)) - sample_mean**2
    return {vals[i]: prob[i] for i in range(2)}

def discrete2_fit_params(discrete_dist):
    x = list(sorted(discrete_dist.keys()))[0]
    p = discrete_dist[x]
    return x, p

def discrete0_x_fit(sample_mean, sample_var):
    x_list = list(range(math.ceil(sample_mean), math.ceil(sample_mean + 5)))
    x = min(x_list, key=lambda v: (sample_mean*v - sample_mean**2 - sample_var) ** 2)
    vals = [0, x]
    prob = [1-sample_mean/x, sample_mean/x]
    var = sum(prob[i]*vals[i]**2 for i in range(2)) - sample_mean**2
    return {vals[i]: prob[i] for i in range(2)}

def discrete0_x_fit_params(discrete_dist):
    x = list(filter(lambda x: x > 0, discrete_dist.keys()))[0]
    p = discrete_dist[x]
    return x, p

def var_distance(sample_var, dist_dict):
    mean = sum(x*dist_dict[x] for x in dist_dict)
    var = sum(x**2*dist_dict[x] for x in dist_dict) - mean**2
    return math.fabs(sample_var - var)

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

case_service = "Cardiac Surgery"
item_id = "38242"
thres = 0.15
occurrence_thres = 15
add_interactions = True

analytics = ScmAnalytics.ScmAnalytics(config.LHS())

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
#surgery_df["procedures_set"] = surgery_df["procedures_set"].apply(lambda s: s.union(set(["CONSTANT"])))

procedure_df = pd.concat([Series(row['event_id'], row['procedures_set']) for _, row in surgery_df.iterrows()],
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
print("Initial List of Procedures and Count of Occurences over {0:d} Surgery Samples".format(len(surg_regres_df)))
print(regression_summary.to_string(index=False))

#regression_summary = regression_summary[regression_summary["occurrences"] > occurrence_thres]

all_procedures = set(regression_summary["procedure"])
procedures = sorted(list(set(regression_summary[regression_summary["occurrences"] > occurrence_thres]["procedure"])))
excluded_procedures = all_procedures - set(procedures)
surg_regres_df["procedure_vector"] = surg_regres_df[[p for p in procedures]].values.tolist()

y = surg_regres_df["used_qty"]
x = np.array(list(surg_regres_df["procedure_vector"]))
results = sm.OLS(y, x).fit()
procedure_mean = {procedures[i]: results.params[i] for i in range(len(procedures))}

while any(p < thres for p in results.params):
    procedures = list(filter(lambda v: procedure_mean[v] >= thres, procedures))
    excluded_procedures = all_procedures - set(procedures)
    surg_regres_df["procedure_vector"] = surg_regres_df[[p for p in procedures]].values.tolist()
    y = surg_regres_df["used_qty"]
    x = np.array(list(surg_regres_df["procedure_vector"]))
    results = sm.OLS(y, x).fit()
    procedure_mean = {procedures[i]: results.params[i] for i in range(len(procedures))}

print(results.summary(xname=procedures))
excluded_procedures = all_procedures - set(procedures)
surg_regres_df["procedure_vector"] = surg_regres_df.apply(
    lambda row: row["procedure_vector"]+[float(any(row[excluded_procedures]))],
    axis=1
)
procedures.append("UNION")
y = surg_regres_df["used_qty"]
x = np.array(list(surg_regres_df["procedure_vector"]))
results = sm.OLS(y, x).fit()
procedure_mean = {procedures[i]: results.params[i] for i in range(len(procedures))}
print(results.summary(xname=procedures))

regression_summary = regression_summary[regression_summary["procedure"].isin(procedures)]
regression_summary = regression_summary.append(pd.DataFrame({"procedure": ["UNION"], "occurrences": [0]}),
                                               ignore_index=True,
                                               sort=False)
regression_summary["mean"] = list(results.params)
# Fit the second moments by estimating E[Y^2|X]
y_var = (surg_regres_df["used_qty"]-results.fittedvalues)**2
res = scipy.optimize.lsq_linear(x, y_var, bounds=(0, np.inf))
print(res)
regression_summary["variance"] = res.x

global_mean = "Global_Mean={:1.2f}".format(np.mean(y))
plt.hist(y - results.fittedvalues, bins=list(np.arange(-10,10,1)), rwidth=0.94, alpha=0.5, label="LS_estimator")
plt.hist(y - [np.mean(y)]*len(y), bins=list(np.arange(-10,10,1)), rwidth=0.94, alpha=0.5, label=global_mean)
plt.legend()
#plt.show()

# fit procedure mu var pairs to discrete probability distributions
for f in [binom_fit, discrete2_fit, discrete0_x_fit]:
    dist = f.__name__
    regression_summary[dist] = regression_summary.apply(lambda row: f(row['mean'], row['variance']), axis=1)
    regression_summary[dist+"_err"] = regression_summary.apply(lambda row: var_distance(row['variance'], row[dist]),
                                                               axis=1)
fit_cols = list(f.__name__ for f in [binom_fit, discrete2_fit, discrete0_x_fit])
regression_summary["best_fit"] = regression_summary.apply(
    lambda row: min(fit_cols, key=lambda x: var_distance(row["variance"], row[x])), axis=1)
regression_summary["var_error_ratio"] = regression_summary.apply(
    lambda row: row[row["best_fit"]+"_err"]/row["variance"], axis=1)


def fit_params(row):
    param_lkup = {"binom_fit": binom_fit_params,
                  "discrete2_fit": discrete2_fit_params,
                  "discrete0_x_fit": discrete0_x_fit_params}
    return param_lkup[row["best_fit"]](row[row["best_fit"]])


regression_summary["binom_fit_err"] = regression_summary.apply(
    lambda row: row[row["best_fit"]+"_err"]/row["variance"], axis=1)

regression_summary["best_fit_params"] = regression_summary.apply(lambda row: fit_params(row), axis=1)

prnt_cols = ["procedure", "occurrences", "mean", "variance", "best_fit", "best_fit_params", "var_error_ratio"]
print(regression_summary[prnt_cols].to_string(index=False))

regression_summary["usage_dist_list"] = regression_summary.apply(
    lambda row:
    [e for sublist in [int(1000 * row[row["best_fit"]][x]) * [x] for x in row[row["best_fit"]]] for e in sublist],
    axis=1
)

scale = 10
procedure_usage = list(regression_summary["usage_dist_list"])
fitted_usage_per_surgery_dist = surg_regres_df[["event_id", "procedure_vector"]]
fitted_usage_per_surgery_dist["usage_dist_list"] = fitted_usage_per_surgery_dist.apply(
    lambda row: [
        sum(np.random.choice(procedure_usage[i])*row["procedure_vector"][i] for i in range(len(procedures)))
        for _ in range(scale)
    ],
    axis=1)

plt.close()
plt.hist([e for s in scale*[y] for e in s],  bins=list(np.arange(0,10,1)), rwidth=0.94, alpha=0.5, label="Raw Data")
plt.hist([e for s in fitted_usage_per_surgery_dist["usage_dist_list"] for e in s],
         bins=list(np.arange(0,10,1)), rwidth=0.94, alpha=0.5, label="Fitted Distribution")
plt.legend()
plt.title("Item Usage Distribution by Surgeries item_id:{0} caseService:{1}".format(item_id, case_service))
plt.xlabel("Items Used Per Surgery")
plt.ylabel("Frequency (Surgeries Count)")
plt.show()

