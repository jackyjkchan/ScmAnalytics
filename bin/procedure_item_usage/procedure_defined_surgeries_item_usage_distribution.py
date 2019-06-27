import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import scipy
import math
import os

from scm_analytics import ScmAnalytics, config
from scipy import stats, optimize, interpolate
from matplotlib.ticker import FormatStrFormatter
from pandas import Series
from scipy.stats import poisson
from textwrap import wrap


def run(case_service="Cardiac Surgery",
        item_id="38242",
        thres=10,
        procedures=set()
        ):
    assert(isinstance(item_id, str))
    max_len = 50

    n_cols = 3
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

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

    if procedures:
        surgery_df = surgery_df["procedures"].apply(lambda x: x.intersection(procedures))
    surgery_df["procedures"] = surgery_df["procedures"].apply(lambda x: frozenset(x))
    surgery_df = surgery_df.join(usage_df[["event_id", "used_qty"]].set_index("event_id"),
                                 on="event_id",
                                 how="left")
    surgery_df["used_qty"] = surgery_df["used_qty"].fillna(0)

    case_df = surgery_df.groupby(["procedures"])\
                        .agg({"used_qty": lambda x: list(x)})\
                        .reset_index()
    case_df["occurrences"] = case_df["used_qty"].apply(lambda x: len(x))
    case_df = case_df[case_df["occurrences"] > thres]

    n_rows = math.ceil(len(case_df) / n_cols)

    fig, ax = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(8.5*2, 11*3))
    print(len(case_df))
    for row in range(n_rows):
        for col in range(n_cols):
            i = row*n_cols + col
            if not i < len(case_df):
                ax[row-1][col].set_xlabel("Items Used")
                continue

            max_val = int(max(case_df.iloc[i]["used_qty"]))
            mean = np.mean(case_df.iloc[i]["used_qty"])
            bins, x_ticks = range(max_val + 2), range(max_val+1)

            ax[row][col].hist(case_df.iloc[i]["used_qty"],
                              bins=bins,
                              density=True,
                              color='C0',
                              alpha=0.5,
                              rwidth=0.96,
                              label="Empirical")

            poisson_fit = ax[row][col].plot([x + 0.5 for x in bins], poisson.pmf(bins, mean),
                                             'o',
                                             ms=8,
                                             alpha=0.5,
                                             color='C1',
                                             label="Poisson")
            ax[row][col].vlines([x + 0.5 for x in bins],
                                0,
                                poisson.pmf(bins, mean),
                                color='C1',
                                lw=5,
                                alpha=0.5)
            title = ", ".join(case_df.iloc[i]["procedures"])
            title = "\n".join(wrap( title, max_len))
            ax[row][col].set_title(title)
            ax[row][col].legend()
            ax[row][col].set_xticks([x + 0.5 for x in bins])
            ax[row][col].set_xticklabels([str(x) for x in bins])

            if row == n_rows-1:
                ax[row][col].set_xlabel("Items Used")
            if col == 0:
                ax[row][col].set_ylabel("Prob. Mass")

    plt.tight_layout()
    plt.savefig("Item_Usage_Distributions/Item_Usage_Distribution_Samples_{0}_{1}.png".format(case_service, item_id), format="png")


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
           84364]
    ids = [129636]
    for id in ids:
        run(item_id=str(id))
