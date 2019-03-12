import simpy
import random
from pprint import pprint
import pandas as pd
from numpy import mean, std
import matplotlib.pyplot as plt
from os import path, makedirs

from scm_simulation.rng_classes import GenerateDeterministic, GenerateFromSample
from scm_simulation.order_policies import DeterministicConDOIPolicyV2, DeterministicConDOIPolicyV2WithoutSchedule
from scm_simulation.run_sim import run_booked_surgery_driven_simulation, Booked_Surgery_Config

from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.PoMetrics import OrderLeadTimeDiscreteDistribution
from scm_analytics.metrics.UsageMetrics import ItemUsagePerDayDistribution
from scm_analytics.metrics.SurgeryMetrics import SurgeriesPerDayDistribution

item_id = "38197"
condoi_level = 6

results_dir = path.join("booked_surgery_results", "{0}_condoi={1}".format(item_id, condoi_level))
if not path.exists(results_dir):
    makedirs(results_dir)

analytics = ScmAnalytics.ScmAnalytics(config.LHS())
usage_df = analytics.usage.get_pref_item_fill_surgery_labels(item_id, analytics.case_cart.df)

surgeries = set(usage_df["fill_qty"])
flag_0 = True if 0 in surgeries else False
if flag_0:
    surgeries.remove(0)

surgery_item_usage = {}
surgery_stochastic_demand = {}
surgery_booked_demand = {}
for surgery in surgeries:
    label_filter = {"dim": "fill_qty",
                    "op": "eq",
                    "val": surgery}
    urgent_filter = {"dim": "urgent_elective",
                     "op": "eq",
                     "val": "Urgent"}
    elective_filter = {"dim": "urgent_elective",
                       "op": "eq",
                       "val": "Elective"}

    urgent_surgery_demand_dist = SurgeriesPerDayDistribution().get_data(usage_df, filters=[label_filter,
                                                                                           urgent_filter]
                                                                        )
    surgery_stochastic_demand[surgery] = GenerateFromSample(list(urgent_surgery_demand_dist))

    elective_surgery_demand_dist = SurgeriesPerDayDistribution().get_data(usage_df, filters=[label_filter,
                                                                                             elective_filter]
                                                                          )
    surgery_booked_demand[surgery] = GenerateFromSample(list(elective_surgery_demand_dist))

    item_stochastic_demand_sample = list(usage_df[usage_df["fill_qty"] == surgery]["used_qty"])
    surgery_item_usage[surgery] = {item_id: GenerateFromSample(list(item_stochastic_demand_sample))}

order_lead_time_sample = OrderLeadTimeDiscreteDistribution() \
        .set_x_units("days") \
        .get_data(analytics.po.df, filters={"dim": "item_id",
                                             "op": "eq",
                                             "val": item_id}
                  )
order_lead_time_sample = list(order_lead_time_sample)
item_demand_sample = ItemUsagePerDayDistribution().set_item_id(item_id).get_data(usage_df,
                                                                                 filters={"dim": "fill_qty",
                                                                                          "op": "eq",
                                                                                          "val": 0}
                                                                                 )
item_stochastic_demand_sample = {item_id: GenerateFromSample(list(item_demand_sample))}

config = Booked_Surgery_Config(
    item_ids=[item_id],
    surgeries=surgeries,
    ordering_policies={item_id: DeterministicConDOIPolicyV2(item_id, constant_days=condoi_level)},
    #ordering_policies={item_id: DeterministicConDOIPolicyV2WithoutSchedule(item_id, constant_days=condoi_level)},
    item_delivery_times={item_id: GenerateFromSample(order_lead_time_sample)},
    initial_inventory={item_id: 0},
    outstanding_orders={item_id: set()},
    surgery_item_usage=surgery_item_usage,
    surgery_stochastic_demand=surgery_stochastic_demand,
    surgery_booked_demand=surgery_booked_demand,
    item_stochastic_demands=item_stochastic_demand_sample
)

print("=================== START REPORT===================")
print("conDOI Level:", condoi_level)
hospital = run_booked_surgery_driven_simulation(config, show=True)
for surgery in surgeries:
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


title = "Distribution of Item({0}) Demand per Day Label For Unlabelled Surgeries".format(str(item_id))
analytics.discrete_distribution_plt(item_demand_sample,
                                        show=False,
                                        save_dir=results_dir,
                                        title=title,
                                        x_label="Number Of Items Consumed",
                                        y_label="Frequency (Days)")
title = "Distribution of Item({0}) Lead Times".format(str(item_id))
analytics.discrete_distribution_plt(order_lead_time_sample,
                                        show=False,
                                        save_dir=results_dir,
                                        title=title,
                                        x_label="Lead Time in (Days)",
                                        y_label="Frequency (POs)")

inventory = hospital.historical_inventory_levels[item_id]
f, axes = plt.subplots(3, 1, figsize=(16, 15))
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
#splt.show()
plt.savefig(path.join(results_dir, title+".svg"),
            format='svg',
            orientation='landscape',
            papertype='letter')
print("======================== END ========================")