import simpy
import random
from pprint import pprint
import pandas as pd
from numpy import mean, std
import matplotlib.pyplot as plt

from scm_simulation.rng_classes import GenerateDeterministic, GenerateFromSample
from scm_simulation.simulation_processes import *
from scm_simulation.order_policies import *
from scm_simulation.hospital import Hospital

from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.PoMetrics import OrderLeadTimeDiscreteDistribution
from scm_analytics.metrics.UsageMetrics import ItemUsagePerDayDistribution


RANDOM_SEED = 0
SIM_TIME = 3600


def main(item_id, lead_time_sample, demand_sample, policy=DeterministicConDOIPolicy, condoi_level=4):
    condoi_level = condoi_level
    item_ids = [item_id]

    ordering_policies = {
        item_id: policy(item_id, constant_days=condoi_level)
    }

    item_delivery_times = {
        item_id: GenerateFromSample(lead_time_sample)
    }

    initial_inventory = {
        item_id: int(mean(demand_sample)*condoi_level)
    }

    outstanding_orders = {
        item_id: set()
    }

    item_stochastic_demands = {
        item_id: GenerateFromSample(demand_sample)
    }

    random.seed(RANDOM_SEED)
    hospital = Hospital(item_ids,
                        ordering_policies,
                        item_delivery_times,
                        item_stochastic_demands,
                        initial_inventory,
                        outstanding_orders)

    env = simpy.Environment()

    env.process(place_order(env, ordering_policies, item_delivery_times, hospital))
    env.process(demand_stochastic(env, item_stochastic_demands, hospital))
    env.process(hospital_bookkeeping(env, hospital))
    env.run(until=SIM_TIME)
    print("historical inventory levels")
    print(hospital.historical_inventory_levels)
    print("average inventory levels")
    print(mean(hospital.historical_inventory_levels[item_id]))
    print("std inventory levels")
    print(std(hospital.historical_inventory_levels[item_id]))
    print("average days of inventory")
    print(mean(hospital.historical_inventory_levels[item_id])/mean(demand_sample))
    print("Item stock out events")
    pprint(hospital.stockouts)
    print("order history")
    print(hospital.historical_orders)

    days_of_inventory = hospital.historical_inventory_levels[item_id]/hospital.item_stochastic_demands[item_id].mean()

    f, axes = plt.subplots(2, 1)
    axes[0].hist(days_of_inventory,
                    bins=range(0, int(max(days_of_inventory)+1)))
    axes[0].set_title("Distribution of Days of Inventory")
    axes[0].set_xlabel("Days of Inventory")
    axes[0].set_ylabel("Freq")

    axes[1].step(range(0, len(hospital.historical_inventory_levels[item_id])),
                 hospital.historical_inventory_levels[item_id],
                 label="Inventory Level")
    axes[1].step(range(0, len(hospital.historical_demand[item_id])),
                 hospital.historical_demand[item_id],
                 label="Demand")
    axes[1].step(range(0, len(hospital.historical_orders[item_id])),
                 hospital.historical_orders[item_id],
                 label="Order Placed")
    axes[1].step(range(0, len(hospital.historical_deliveries[item_id])),
                 hospital.historical_deliveries[item_id],
                 label="Delivery")
    axes[1].set_title("Inventory Time Trend")
    axes[1].legend()
    plt.show()
    return


if __name__ == "__main__":
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())
    item_df = analytics.classify_usage_items()
    item_df = item_df[item_df["used_qty"] > 2000]
    item_ids = list(item_df.head(10)["item_id"])
    item_id = "4694"

    item_filter = {"dim": "item_id",
                      "op": "eq",
                      "val": item_id}

    x_units = "days"
    order_lead_time_sample = OrderLeadTimeDiscreteDistribution() \
        .set_x_units(x_units) \
        .get_data(analytics.po.df, filters=item_filter)

    item_demand_sample = ItemUsagePerDayDistribution().set_item_id(item_id).get_data(analytics.usage.df)
    analytics.discrete_distribution_plt(item_demand_sample,
                                        show=True,
                                        title="Daily Item Demand Distribution")

    analytics.discrete_distribution_plt(order_lead_time_sample,
                                        show=True,
                                        title="Order Lead Time Distribution")

    main(item_id, [3], list(item_demand_sample), policy=DeterministicConDOIPolicy, condoi_level=10)
