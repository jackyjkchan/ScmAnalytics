from numpy import mean, std
import matplotlib.pyplot as plt
from os import path, makedirs

from scm_simulation.rng_classes import GenerateFromSample, GenerateDeterministic
from scm_simulation.order_policies import DeterministicConDOIPolicyV2, DeterministicConDOIPolicyV2WithoutSchedule
from scm_simulation.run_sim import run_booked_surgery_driven_simulation, Booked_Surgery_Config

from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.PoMetrics import OrderLeadTimeDiscreteDistribution
from scm_analytics.metrics.UsageMetrics import ItemUsagePerDayDistribution
from scm_analytics.metrics.SurgeryMetrics import SurgeriesPerDayDistribution
from scipy.stats import sem, t


def estimator_95confi(data):
    n = len(data)
    m = mean(data)
    std_err = sem(data)
    h = std_err * t.ppf((1 + 0.95) / 2, n - 1)
    return h/m


levels = [1, 1.25, 1.5, 1.75, 2, 2.33, 2.66, 3, 3.5, 4, 5, 6, 9]

policies_under_test = {
    "WithSchedule": DeterministicConDOIPolicyV2,
    "WithoutSchedule": DeterministicConDOIPolicyV2WithoutSchedule
}

item_ids = [
"1122",
"1308",
"35893",
"36298",
"36556",
"36560",
"36592",
"38160",
"38226",
"38286",
"38421",
"38425",
"61565",
"75937",
"76057",
"80192",
"81812",
"85321",
"133221",
"51678",
]

item_ids = [
"36592",
"38160",
"38226",
"38286",
"38421",
"38425",
"61565",
"75937",
"76057",
"80192",
"81812",
"85321",
"133221",
"51678",
]

for item_id in item_ids:

    results_dir = path.join("results", item_id)
    if not path.exists(results_dir):
        makedirs(results_dir)

    analytics = ScmAnalytics.ScmAnalytics(config.LHS())
    usage_df = analytics.usage.get_pref_item_fill_surgery_labels(item_id, analytics.case_cart.df)
    surgeries = set(usage_df["fill_qty"])

    if 0 in surgeries:
        surgeries.remove(0)

    for surgery in sorted(surgeries, reverse=True):
        print(surgery, len(usage_df[usage_df["fill_qty"] == surgery]))
        if len(usage_df[usage_df["fill_qty"] == surgery]) < 25:
            usage_df[["fill_qty"]] = usage_df[["fill_qty"]].replace(surgery, surgery-1)

    surgeries = set(usage_df["fill_qty"])
    if 0 in surgeries:
        surgeries.remove(0)
    usage_df["start_date"] = usage_df["start_dt"].apply(lambda x: x.date())
    surg_dist_args = {"start": min(usage_df["start_date"]),
                      "end": max(usage_df["start_date"])}
    surgery_item_usage = {}
    surgery_stochastic_demand = {}
    surgery_booked_demand = {}
    for surgery in surgeries:
        print(surgery)
        label_filter = {"dim": "fill_qty",
                        "op": "eq",
                        "val": surgery}
        urgent_filter = {"dim": "urgent_elective",
                         "op": "eq",
                         "val": "Urgent"}
        elective_filter = {"dim": "urgent_elective",
                           "op": "eq",
                           "val": "Elective"}
        urgent_surgery_demand_dist = SurgeriesPerDayDistribution().get_data(usage_df,
                                                                            filters=[label_filter,
                                                                                     urgent_filter],
                                                                            args=surg_dist_args)
        surgery_stochastic_demand[surgery] = GenerateFromSample(list(urgent_surgery_demand_dist))

        elective_surgery_demand_dist = SurgeriesPerDayDistribution().get_data(usage_df,
                                                                              filters=[label_filter,
                                                                                       elective_filter],
                                                                              args=surg_dist_args
                                                                              )
        surgery_booked_demand[surgery] = GenerateFromSample(list(elective_surgery_demand_dist))

        item_stochastic_demand_sample = list(usage_df[usage_df["fill_qty"] == surgery]["used_qty"])
        surgery_item_usage[surgery] = {item_id: GenerateFromSample(list(item_stochastic_demand_sample))}

        title = "Distribution of Urgent Surgeries per Day Label={0}".format(str(surgery))
        analytics.discrete_distribution_plt(surgery_stochastic_demand[surgery].samples,
                                            show=False,
                                            save_dir=results_dir,
                                            title=title,
                                            x_label="Number of Surgeries in a Day",
                                            y_label="Frequency (Days)")
        title = "Distribution of Elective Surgeries per Day Label={0}".format(str(surgery))
        analytics.discrete_distribution_plt(surgery_booked_demand[surgery].samples,
                                            show=False,
                                            save_dir=results_dir,
                                            title=title,
                                            x_label="Number of Surgeries in a Day",
                                            y_label="Frequency (Days)")
        title = "Item Usage Distribution by Surgeries Label={0}".format(str(surgery))
        analytics.discrete_distribution_plt(surgery_item_usage[surgery][item_id].samples,
                                            show=False,
                                            save_dir=results_dir,
                                            title=title,
                                            x_label="Number of Items Used in a Case",
                                            y_label="Frequency (Cases)")

    order_lead_time_sample = OrderLeadTimeDiscreteDistribution() \
            .set_x_units("days") \
            .get_data(analytics.po.df, filters={"dim": "item_id",
                                                 "op": "eq",
                                                 "val": item_id})
    order_lead_time_sample = list(order_lead_time_sample)
    if mean(order_lead_time_sample) > 1:
        title = "Distribution of Item({0}) Lead Times".format(str(item_id))
        analytics.discrete_distribution_plt(order_lead_time_sample,
                                            show=False,
                                            save_dir=results_dir,
                                            title=title,
                                            x_label="Lead Time in (Days)",
                                            y_label="Frequency (POs)")
        lead_time_rng = GenerateFromSample(order_lead_time_sample)
    else:
        lead_time_rng = GenerateDeterministic(2)
    item_demand_sample = ItemUsagePerDayDistribution().set_item_id(item_id).get_data(usage_df,
                                                                                     filters={"dim": "fill_qty",
                                                                                              "op": "eq",
                                                                                              "val": 0}
                                                                                     )
    item_stochastic_demand_sample = {item_id: GenerateFromSample(list(item_demand_sample))}
    title = "Distribution of Item({0}) Demand per Day Label For Unlabelled Surgeries".format(str(item_id))
    analytics.discrete_distribution_plt(item_demand_sample,
                                            show=False,
                                            save_dir=results_dir,
                                            title=title,
                                            x_label="Number Of Items Consumed",
                                            y_label="Frequency (Days)")

    average_stockouts_rates = {"WithSchedule": [],
                         "WithoutSchedule": []}
    average_inventory = {"WithSchedule": [],
                         "WithoutSchedule": []}

    for policy in policies_under_test:

        for condoi_level in levels:
            initial = True
            stockout_rate = []
            inventory_levels = []

            sim_config = Booked_Surgery_Config(
                item_ids=[item_id],
                surgeries=surgeries,
                ordering_policies={item_id: policies_under_test[policy](item_id, constant_days=condoi_level)},
                item_delivery_times={item_id: lead_time_rng},
                initial_inventory={item_id: 0},
                outstanding_orders={item_id: set()},
                surgery_item_usage=surgery_item_usage,
                surgery_stochastic_demand=surgery_stochastic_demand,
                surgery_booked_demand=surgery_booked_demand,
                item_stochastic_demands=item_stochastic_demand_sample
            )

            while len(stockout_rate) < 5 or estimator_95confi(stockout_rate) > 0.05:
                if len(stockout_rate) > 2:
                    print(estimator_95confi(stockout_rate))
                if len(stockout_rate) > 20:
                    break
                hospital = run_booked_surgery_driven_simulation(sim_config, show=True, SIM_TIME=10100, WARMUP=100)

                inventory = hospital.historical_inventory_levels[item_id]
                inventory_levels.append(mean(hospital.historical_inventory_levels[item_id]))
                stockout_rate.append(len(hospital.stockouts[item_id])/10000)

                if initial and condoi_level == 5:
                    f, axes = plt.subplots(3, 1, figsize=(16, 18))
                    axes[0].hist(inventory,
                                bins=range(0, int(max(inventory)+1)))
                    axes[0].set_title("Distribution of Inventory Level")
                    axes[0].set_xlabel("Inventory Level")
                    axes[0].set_ylabel("Freq")

                    axes[1].hist(hospital.historical_demand[item_id],
                                bins=range(0, int(max(hospital.historical_demand[item_id]))+1))
                    axes[1].set_title("Distribution of Realized Demand")
                    axes[1].set_xlabel("Realized Demand")
                    axes[1].set_ylabel("Freq")

                    axes[2].step(range(0, len(hospital.historical_inventory_levels[item_id])),
                                 hospital.historical_inventory_levels[item_id],
                                 linestyle="solid",
                                 label="Inventory Level")
                    axes[2].step(range(0, len(hospital.historical_demand[item_id])),
                                 hospital.historical_demand[item_id],
                                 linestyle="dashed",
                                 label="Demand")
                    axes[2].step(range(0, len(hospital.historical_orders[item_id])),
                                 hospital.historical_orders[item_id],
                                 linestyle="dashdot",
                                 label="Order Placed")
                    axes[2].step(range(0, len(hospital.historical_deliveries[item_id])),
                                 hospital.historical_deliveries[item_id],
                                 linestyle="dotted",
                                 label="Delivery")
                    title = "Inventory Trace, Average Demand={0:0.2f}, Inv_Level={1:0.2f}, Days_Of_Inv={2:0.2f}"\
                        .format(mean(hospital.historical_demand[item_id]),
                                mean(hospital.historical_inventory_levels[item_id]),
                                mean(hospital.historical_inventory_levels[item_id])/mean(hospital.historical_demand[item_id]))
                    axes[2].set_title(title)
                    axes[2].legend()
                    #plt.show()
                    plt.savefig(path.join(results_dir, title+".svg"),
                                format='svg',
                                orientation='landscape',
                                papertype='letter')
                    plt.close()
                initial = False

            print("Policy:{0}, conDOI:{1}, StockoutRate:{2}, 95%ConfiRatio:{3}".format(policy,
                                                                                      str(condoi_level),
                                                                                      str(mean(stockout_rate)),
                                                                                      str(estimator_95confi(stockout_rate))
                                                                                      ))
            print(std(stockout_rate))
            average_stockouts_rates[policy].append(mean(stockout_rate))
            average_inventory[policy].append(mean(inventory_levels))

    plt.figure(figsize=(16, 8))
    plt.plot(average_inventory["WithSchedule"],
             average_stockouts_rates["WithSchedule"],
             "-x",
             label="WithSchedule")
    plt.plot(average_inventory["WithoutSchedule"],
             average_stockouts_rates["WithoutSchedule"],
             "-o",
             label="WithoutSchedule")
    plt.title("Stockout Rate vs Inventory Level item_id:{0}".format(item_id))
    plt.xlabel("Average Inventory Level")
    plt.ylabel("stock out rate")
    plt.legend()
    plt.savefig(path.join(results_dir, "policy_comparison.svg"),
                format='svg',
                orientation='landscape',
                papertype='letter')
    plt.close()
