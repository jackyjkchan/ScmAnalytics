from numpy import mean, std, random
from multiprocessing import Pool
import matplotlib.pyplot as plt
from os import path, makedirs
from math import sqrt

from scm_simulation.rng_classes import GenerateFromSample, GenerateDeterministic, GenerateFromScaledLogNormal
from scm_simulation.order_policies import DeterministicConDOIPolicyV2, DeterministicConDOIPolicyV2WithoutSchedule, \
    POUTPolicy, POUTPolicyWithoutSchedule
from scm_simulation.hospital import HospitalPreGenerated
from scm_simulation.run_sim import Booked_Surgery_Config, run_pre_generated_rv_sim, run_pre_generated_hospital

from scm_analytics import ScmAnalytics, config
import datetime


def create_hospital(config, seed):
    hospital = HospitalPreGenerated(config.item_ids,
                                    config.ordering_policies,
                                    config.item_delivery_times,
                                    config.item_stochastic_demands,
                                    config.initial_inventory,
                                    config.outstanding_orders,
                                    config.surgeries)
    hospital.set_surgery_item_usage(config.surgery_item_usage)
    hospital.set_surgery_stochastic_demand(config.surgery_stochastic_demand)
    hospital.set_booked_surgery_stochastic_demand(config.surgery_booked_demand)
    hospital.set_sim_time(10500)
    hospital.setrandomvars(10500, seed=seed)
    return hospital

conD_lvl = 1.5
urgent_ratio = 0.2
lead_times = {"LT_Uni_3_4_5": GenerateFromSample([3, 4, 5])}
lead_time_config = "LT_Uni_3_4_5"
lead_time_rng = lead_times[lead_time_config]
base_dir = "single_run_20180418"

item_id = "item1"
policies = {"ConDOIWithSchedule": DeterministicConDOIPolicyV2(item_id, constant_days=conD_lvl),
            "ConDOIWithoutSchedules": DeterministicConDOIPolicyV2WithoutSchedule(item_id,
                                                                                 constant_days=conD_lvl),
            "PoutWithSchedule": POUTPolicy(item_id, 0.8, conD_lvl * 8),
            "PoutWithoutSchedule": POUTPolicyWithoutSchedule(item_id, 0.8, conD_lvl * 8)}

policy = "ConDOIWithSchedule"

results_dir = path.join(base_dir,
                        "{0}_lvl={1}_urgent_rate={2}_{3}".format(policy,
                                                                 conD_lvl,
                                                                 urgent_ratio,
                                                                 lead_time_config))
if not path.exists(results_dir):
    makedirs(results_dir)

surgeries = ["A", "B"]
surgery_item_usage = {"A": {item_id: GenerateDeterministic(1)},
                      "B": {item_id: GenerateFromSample([1, 2])}}

surgery_stochastic_demand = {"A": GenerateFromScaledLogNormal(2, 0.5, urgent_ratio),
                             "B": GenerateFromSample([0])}
surgery_booked_demand = {"A": GenerateFromScaledLogNormal(2, 0.5, 1 - urgent_ratio),
                         "B": GenerateFromScaledLogNormal(2, 0.5, 1)}
item_delivery_times = {item_id: lead_time_rng}

sim_config = Booked_Surgery_Config(
    item_ids=[item_id],
    surgeries=surgeries,
    ordering_policies={item_id: policies[policy]},
    item_delivery_times=item_delivery_times,
    initial_inventory={item_id: 0},
    outstanding_orders={item_id: set()},
    surgery_item_usage=surgery_item_usage,
    surgery_stochastic_demand=surgery_stochastic_demand,
    surgery_booked_demand=surgery_booked_demand,
    item_stochastic_demands={item_id: GenerateDeterministic(0)})

print("=================== START REPORT ===================")
print("Level:", conD_lvl)
print("Policy:", policy)
hospital = create_hospital(sim_config, 0)
hospital = run_pre_generated_hospital(hospital)
analytics = ScmAnalytics.ScmAnalytics(config.LHS())
for surgery in surgeries:
    title = "Distribution of Urgent Surgeries per Day Label={0}".format(str(surgery))
    analytics.discrete_distribution_plt(surgery_stochastic_demand[surgery].sample(1000),
                                        show=False,
                                        save_dir=results_dir,
                                        title=title,
                                        x_label="Number of Surgeries in a Day",
                                        y_label="Frequency (Days)")

    title = "Distribution of Elective Surgeries per Day Label={0}".format(str(surgery))
    analytics.discrete_distribution_plt(surgery_booked_demand[surgery].sample(1000),
                                        show=False,
                                        save_dir=results_dir,
                                        title=title,
                                        x_label="Number of Surgeries in a Day",
                                        y_label="Frequency (Days)")

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
axes[2].set_xlim(200, 250)

title = "Inventory Trace, Average Demand={0:0.2f}, Inv_Level={1:0.2f}, Days_Of_Inv={2:0.2f}"\
    .format(mean(hospital.historical_demand[item_id]),
            mean(hospital.historical_inventory_levels[item_id]),
            mean(hospital.historical_inventory_levels[item_id]) /
            mean(hospital.historical_demand[item_id]))
axes[2].set_title(title)
axes[2].legend()

fn = "Inventory Level Simulation Trace"
plt.savefig(path.join(results_dir, fn+".png"),
            format='png',
            orientation='landscape',
            papertype='letter')
plt.close()