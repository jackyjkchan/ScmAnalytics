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

procedure_df = pd.concat([Series(row['event_id'], row['procedures']) for _, row in surgery_df.iterrows()])\
        .reset_index() \
        .rename(columns={"index": "procedure", 0: "event_id"})\
        .join(surgery_df[['event_id', 'start_date', 'urgent_elective']].set_index('event_id'),
              on="event_id",
              how="left",
              rsuffix="surgery")

procedures = set(procedure_df["procedure"])

surgery_df["procedures"] = surgery_df["procedures"].apply(lambda x: x.intersection(procedures))
start = min(surgery_df["start_date"])
end = max(surgery_df["start_date"])

fig, ax = plt.subplots(nrows=7, ncols=4, figsize=(15, 15))

ax_col = 0
for status in ["Urgent", "Elective"]:
    p_df = procedure_df[procedure_df["urgent_elective"] == status]
    df = pd.DataFrame()
    df["start_date"] = pd.date_range(start=start, end=end, freq='D')
    df["start_date"] = df["start_date"].apply(lambda x: x.date())

    filtered_surg_df = df.join(p_df.groupby(["start_date"]).agg({"event_id": "nunique"}),
                               on="start_date",
                               how="left",
                               rsuffix="procedure").fillna(0)
    filtered_p_df = df.join(p_df.groupby(["start_date"]).agg({"event_id": "count"}),
                            on="start_date",
                            how="left",
                            rsuffix="procedure").fillna(0)

    for df in [filtered_surg_df, filtered_p_df]:
        df["day_of_week"] = analytics.date_to_day_of_week(df, "start_date")

        for i in weekday_map:
            day = weekday_map[i]
            mean = np.mean(df[df["day_of_week"] == day]["event_id"])
            variance = np.var(df[df["day_of_week"] == day]["event_id"])
            print(status, day, mean, variance)
            # cond_df = df[df["event_id"] > 0]
            # print(np.mean(cond_df[cond_df["day_of_week"] == day]["event_id"]),
            #       np.var(cond_df[cond_df["day_of_week"] == day]["event_id"]))
            bins = range(int(max(df["event_id"]))+1)
            xticks = range(int(max(df["event_id"])))

            emp = ax[i][ax_col].hist(df[df["day_of_week"] == day]["event_id"],
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
                          1: "Emergency Procedure",
                          2: "Elective Surgery",
                          3: "Elective Procedure"}
                ax[i][ax_col].set_title(titles[ax_col])
            if ax_col == 0:
                ax[i][ax_col].set_ylabel(weekday_map[i])
            if i == 6:
                ax[i][ax_col].set_xlabel("Demand Per Day")

            #ax[i][ax_col].set_xticks([x + 0.5 for x in bins], bins)

        ax_col += 1
print(emp, poisson_fit)
fig.tight_layout()
plt.savefig("Surgery_Procedure_Demand_Distributions.svg", format="svg")
plt.savefig("Surgery_Procedure_Demand_Distributions.png", format="png")

print(df)