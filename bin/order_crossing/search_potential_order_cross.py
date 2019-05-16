from scm_analytics import ScmAnalytics, config
import numpy as np
from pprint import pprint
import matplotlib.pyplot as plt

analytics = ScmAnalytics.ScmAnalytics(config.LHS())

po_df = analytics.po.df
po_df = po_df[~po_df["stock_status"]]

item_ids = set(po_df["item_id"])
summary_df = po_df.groupby("item_id")\
                  .agg({"po_id": "nunique"})\
                  .reset_index()\
                  .rename(columns={'po_id': 'total_orders_count'})
summary_df["crossed_orders_count"] = 0
summary_df["crossed_PO_ids"] = 0

item_index = 1
cross_cnt = 0

crossed_orders_count = []
crossed_PO_ids = []
for item_id in summary_df["item_id"]:
    crossed_pos = set()
    print(item_index,"/",len(item_ids))
    df = po_df[po_df["item_id"]==item_id]
    df = df.sort_values(["order_date"])

    order_deliveries = list(zip(df["order_date"], df["delivery_date"]))

    for i in range(len(df)):
        #print("{0}/{1}".format(str(i+1), str(len(df))))
        j = i+1
        while j < len(df) and order_deliveries[j][0] <= order_deliveries[i][0]:
            j += 1

        while j < len(df) and order_deliveries[j][0] < order_deliveries[i][1]:
            cross_cnt += 1
            crossed_pos.add(df.iloc[j]["po_id"])
            #print(df.iloc[j])
            j += 1
    item_index += 1
    crossed_orders_count.append(len(crossed_pos))
    crossed_PO_ids.append(crossed_pos)
summary_df["crossed_orders_count"] = crossed_orders_count
summary_df["crossed_PO_ids"] = crossed_PO_ids
summary_df["cross_ratio"] = summary_df["crossed_orders_count"] / summary_df["total_orders_count"]

bins = np.arange(0, 105, step=5)
plt.hist(summary_df["cross_ratio"]*100, bins=bins, rwidth=0.96, alpha=0.5)
plt.xticks(bins)
plt.title("Order Cross Ratio Distribution for all Non-Stock (Non-HMMS) Items")
plt.xlabel("Percentage of 'Total Orders Placed' that were \n "
           + "'Placed While Pending Shipment'")

plt.ylabel("Count of Items")
plt.savefig("order_cross_ratio_summary.svg", format="svg")
print("Average Cross Rate:", sum(summary_df["crossed_orders_count"])/sum(summary_df["total_orders_count"]))

summary_df.to_csv("order_cross_sumamry.csv", ",")