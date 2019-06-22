import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas import Series
from matplotlib.ticker import FormatStrFormatter
from scm_analytics import ScmAnalytics, config
from scipy.stats import poisson

extract_surgeries = True

weekday_map = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }

analytics = ScmAnalytics.ScmAnalytics(config.LHS())

case_service = 'Cardiac Surgery'

surgery_df = analytics.surgery.df
surgery_df = surgery_df.drop_duplicates(subset=["event_id"])
surgery_df = surgery_df[surgery_df["case_service"] == case_service]
surgery_df["start_date"] = surgery_df["start_dt"].apply(lambda x: x.date())
surgery_df["procedure_count"] = surgery_df["procedures"].apply(lambda x: len(x))

max_procedures = max(surgery_df["procedure_count"])

start = min(surgery_df["start_date"])
end = max(surgery_df["start_date"])

fig, ax = plt.subplots(nrows=max_procedures, ncols=2, figsize=(12, 15))

ax_col = 0

for status in ["Urgent", "Elective"]:
    for i in range(max_procedures):
        i_label = i+1
        f_surg_df = surgery_df[(surgery_df["procedure_count"] == i_label) & (surgery_df["urgent_elective"] == status)]

        df = pd.DataFrame()
        df["start_date"] = pd.date_range(start=start, end=end, freq='D')
        df["start_date"] = df["start_date"].apply(lambda x: x.date())

        df = df.join(f_surg_df.groupby(["start_date"]).agg({"event_id": "nunique"}),
                     on="start_date",
                     how="left",
                     rsuffix="procedure").fillna(0)

        mean = np.mean(df["event_id"])
        variance = np.var(df["event_id"])
        print(status, i_label, mean, variance)
        # cond_df = df[df["event_id"] > 0]
        # print(np.mean(cond_df[cond_df["day_of_week"] == day]["event_id"]),
        #       np.var(cond_df[cond_df["day_of_week"] == day]["event_id"]))
        bins = range(max_procedures+1)
        xticks = range(max_procedures)

        emp = ax[i][ax_col].hist(df["event_id"],
                 bins=bins,
                 density=True,
                 color='C0',
                 alpha=0.5,
                 rwidth=0.96,
                 label="Empirical")

        poisson_fit = ax[i][ax_col].plot([x+0.5 for x in bins], poisson.pmf(bins, mean),
                                         'o',
                                         ms=8,
                                         alpha=0.5,
                                         color='C1',
                                         label="Poisson")
        ax[i][ax_col].vlines([x+0.5 for x in bins],
                             0,
                             poisson.pmf(bins, mean),
                             color='C1',
                             lw=5,
                             alpha=0.5)

        ax[i][ax_col].legend()
        ax[i][ax_col].xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        if i == 0:
            titles = {0: "Emergency Surgery",
                      1: "Elective Surgery"}
            ax[i][ax_col].set_title(titles[ax_col])
        if ax_col == 0:
            ax[i][ax_col].set_ylabel("{0:d}-procedure Surgeries".format(i_label))
        if i == max_procedures-1:
            ax[i][ax_col].set_xlabel("Demand Per Day")

        #ax[i][ax_col].set_xticks([x + 0.5 for x in bins], bins)

    ax_col += 1
print(emp, poisson_fit)
fig.tight_layout()
plt.savefig("Surgery_Demand_Distributions_by_proc_cnt.svg", format="svg")
plt.savefig("Surgery_Demand_Distributions_by_proc_cnt.png", format="png")

print(df)