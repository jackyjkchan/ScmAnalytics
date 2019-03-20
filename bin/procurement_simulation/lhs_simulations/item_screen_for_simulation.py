"""
This script looks for items with comparable PO and usage data within the OrangeBag time window as well as filtering
on other attributes
"""
import matplotlib.pyplot as plt
from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.PoMetrics import OrderLeadTimeDiscreteDistribution
from scm_analytics.metrics.UsageMetrics import ItemUsagePerDayDistribution, ItemUsagePerWeekDistribution


def main():
    min_usages = 200
    po_usage_threshold = 0.33

    analytics = ScmAnalytics.ScmAnalytics(config.LHS())
    usage_df = analytics.usage.df
    start = min(usage_df["start_dt"])
    end = max(usage_df["start_dt"])
    po_df = analytics.po.df
    po_df = po_df[po_df["order_date"] >= start]
    po_df = po_df[po_df["order_date"] <= end]

    po_df["leadtime_intdays"] = po_df["order_leadtime"].apply(lambda x: x.days)
    po_summary_df = po_df.groupby(["item_id"]).agg({
        'po_id': {"orders": "nunique"},
        'qty_ea': {"total_order_qty": 'sum'},
        'leadtime_intdays': {"avg_leadtime": 'mean', "std": 'std'}
    }).reset_index()
    po_summary_df.columns = [' '.join(col).strip() for col in po_summary_df.columns.values]
    po_summary_df = po_summary_df.rename(columns={ "po_id orders": "orders_placed",
                                   "qty_ea total_order_qty": "total_order_qty",
                                   "leadtime_intdays avg_leadtime": "leadtime_avg",
                                   "leadtime_intdays std": "leadtime_std"
    })

    usage_df["total_expenditure"] = usage_df["used_qty"] * usage_df["unit_price"]
    item_df = usage_df.groupby(["item_id"]).agg({
        'used_qty': 'sum',
        'total_expenditure': 'sum',
        'unit_price': 'mean',
        'code_name': 'max'
    }).reset_index()

    item_df = item_df.join(po_summary_df.set_index(["item_id"]),
                           on="item_id",
                           how="left",
                           rsuffix="po")

    item_df["usage_order_ratio"] = item_df["used_qty"] / item_df["total_order_qty"]

    filtered_item_df = item_df
    filtered_item_df = filtered_item_df[filtered_item_df["used_qty"] > min_usages]
    filtered_item_df = filtered_item_df[filtered_item_df["usage_order_ratio"] < 1+po_usage_threshold]
    #filtered_item_df = filtered_item_df[filtered_item_df["usage_order_ratio"] > 1-po_usage_threshold]

    fields = ["item_id", "code_name","total_expenditure", "used_qty", "usage_order_ratio"]
    print("".join("{:>30}".format(f) for f in fields))
    for i in range(0, len(filtered_item_df)):
        s = "".join("{:>30}".format(str(filtered_item_df.iloc[i][f])) for f in fields)
        print(s)

    print("Enter item id to analyse")
    id = input()
    while id:
        #id = 1875
        usage_per_day_data = ItemUsagePerDayDistribution().set_item_id(id).get_data(usage_df)
        item_filter = {"dim": "item_id",
                       "op": "eq",
                       "val": id}
        usage_per_week_data = ItemUsagePerWeekDistribution().set_item_id(id).get_data(usage_df)
        order_lead_time_sample = OrderLeadTimeDiscreteDistribution() \
            .set_x_units("days") \
            .get_data(analytics.po.df, filters=item_filter)


        analytics.discrete_distribution_plt(usage_per_day_data,
                                            show=True,
                                            title="Daily Item Demand Distribution")
        plt.hist(usage_per_week_data, bins=15)
        plt.title("Item usage per week, x: uses per week, y: # weeks")
        plt.show()
        # analytics.discrete_distribution_plt(usage_per_week_data,
        #                                     show=True,
        #                                     title="Weekly Item Demand Distribution")
        analytics.discrete_distribution_plt(order_lead_time_sample,
                                            show=True,
                                            title="Order Lead Time Distribution")

        id = input()
    return 1


if __name__ == "__main__":
    main()
