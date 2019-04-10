import simpy
from rng_classes import GenerateDeterministic
from order_policies import *
from hospital import Hospital
from hospital2 import Hospital2
import random
from collections import namedtuple
import numpy as np

RANDOM_SEED = 0

item_sim_config_fields = ["item_ids",
                          "ordering_policies",
                          "item_delivery_times",
                          "initial_inventory",
                          "outstanding_orders",
                          "item_stochastic_demands"]

Item_Sim_Config = namedtuple('Item_Sim_Config', item_sim_config_fields)

stochastic_surgery_sim_config_fields = ["item_ids",
                                        "surgeries",
                                        "ordering_policies",
                                        "item_delivery_times",
                                        "initial_inventory",
                                        "outstanding_orders",
                                        "surgery_item_usage",
                                        "surgery_stochastic_demand",
                                        "item_stochastic_demands"]

Stochastic_Surgery_Config = namedtuple('Stochastic_Surgery_Config', stochastic_surgery_sim_config_fields)

booked_surgery_sim_config_fields = ["item_ids",
                                    "surgeries",
                                    "ordering_policies",
                                    "item_delivery_times",
                                    "initial_inventory",
                                    "outstanding_orders",
                                    "surgery_item_usage",
                                    "surgery_stochastic_demand",
                                    "surgery_booked_demand",
                                    "item_stochastic_demands"]

Booked_Surgery_Config = namedtuple('Booked_Surgery_Config', booked_surgery_sim_config_fields)


def run_pout_sim(config1, booking_lead_time,  simtime=10000, warmup=500, show=False):

    random.seed(RANDOM_SEED)
    hospital = Hospital2(config1.item_ids,
                         config1.ordering_policies,
                         config1.item_delivery_times,
                         config1.item_stochastic_demands,
                         config1.initial_inventory,
                         config1.outstanding_orders,
                         config1.surgeries)
    hospital.set_surgery_item_usage(config1.surgery_item_usage)
    hospital.set_surgery_stochastic_demand(config1.surgery_stochastic_demand)
    hospital.set_booked_surgery_stochastic_demand(config1.surgery_booked_demand)
    hospital.set_sim_time(simtime)
    hospital.clean_data(warmup)
    hospital.setrandomvars(simtime)
    for i in range(0, simtime):
        for item in hospital.item_ids:
            # Receive order
            hospital.inventory[item] += hospital.historical_deliveries[item][i]
            # Item demand from surgeries
            for surgery in hospital.surgeries:
                usage = hospital.new_surgery_item_usage[surgery][item][i]
                hospital.historical_demand[item][i] += usage
                if hospital.inventory[item] < usage:
                    hospital.inventory[item] = 0
                    hospital.stockouts[item].append(i)
                else:
                    hospital.inventory[item] -= usage
            # Book surgeries
            for surgery in hospital.surgeries:
                if len(hospital.surgery_schedule[surgery]) > i + booking_lead_time:
                    hospital.surgery_schedule[surgery][i + booking_lead_time] += hospital.sum_surgery[surgery][i]
            # Place order
            order_qty = config1.ordering_policies[item].action(i, hospital)
            hospital.orders[item].add((i, order_qty))
            hospital.historical_orders[item][i] += order_qty
            delivery_time = hospital.new_lead_times[item][i]
            if i + delivery_time < len(hospital.historical_deliveries[item]):
                hospital.historical_deliveries[item][i + delivery_time] += order_qty
            # Hospital bookkeeping
            hospital.historical_inventory_levels[item][i] += hospital.inventory[item]
    if show:
        print("Average Inventory Level")
        for item_id in config.item_ids:
            print("{0}: {1}".format(item_id, str(np.mean(hospital.historical_inventory_levels[item_id]))))
        for item in hospital.stockouts:
            print("{0}: {1}".format(item, len(hospital.stockouts[item])))
        print(hospital.stockouts)
    return hospital


def run_item_driven_simulation(config1, simtime=10000, show=False):
    item_ids = config1.item_ids
    ordering_policies = config1.ordering_policies
    item_delivery_times = config1.item_delivery_times
    initial_inventory = config1.initial_inventory
    outstanding_orders = config1.outstanding_orders
    item_stochastic_demands = config1.item_stochastic_demands
    random.seed(RANDOM_SEED)
    hospital = Hospital(item_ids,
                        ordering_policies,
                        item_delivery_times,
                        item_stochastic_demands,
                        initial_inventory,
                        outstanding_orders)
    env = simpy.Environment()
    # env.process(receive_order(env, hospital))
    # env.process(item_demand(env, item_stochastic_demands, hospital))
    # env.process(place_order(env, ordering_policies, item_delivery_times, hospital))
    # env.process(hospital_bookkeeping(env, hospital))
    env.run(until=simtime)
    if show:
        print("Average Inventory Level")
        for item_id in item_ids:
            print("{0}: {1}".format(item_id, str(np.mean(hospital.historical_inventory_levels[item_id]))))

    return hospital


def run_stochastic_surgery_driven_simulation(config1, simtime=100000, warmup=500, show=False):
    item_ids = config1.item_ids
    ordering_policies = config1.ordering_policies
    item_delivery_times = config1.item_delivery_times
    initial_inventory = config1.initial_inventory
    outstanding_orders = config1.outstanding_orders
    random.seed(RANDOM_SEED)
    hospital = Hospital(item_ids,
                        ordering_policies,
                        item_delivery_times,
                        {},
                        initial_inventory,
                        outstanding_orders,
                        surgeries=config1.surgeries)
    hospital.set_surgery_item_usage(config1.surgery_item_usage)
    hospital.set_surgery_stochastic_demand(config1.surgery_stochastic_demand)
    hospital.set_sim_time(simtime)
    env = simpy.Environment()
    # env.process(receive_order(env, hospital))
    # env.process(item_demand_from_surgeries(env, hospital))
    # env.process(place_order(env, ordering_policies, item_delivery_times, hospital))
    # env.process(hospital_bookkeeping(env, hospital))
    env.run(until=simtime)
    hospital.clean_data(warmup)
    if show:
        print("Average Inventory Level")
        for item_id in item_ids:
            print("{0}: {1}".format(item_id, str(np.mean(hospital.historical_inventory_levels[item_id]))))
        for item in hospital.stockouts:
            print("{0}: {1}".format(item, len(hospital.stockouts[item])))
        print(hospital.stockouts)
    return hospital


def run_booked_surgery_driven_simulation(config1, simtime=100000, warmup=500, show=False):
    item_ids = config1.item_ids
    ordering_policies = config1.ordering_policies
    item_delivery_times = config1.item_delivery_times
    initial_inventory = config1.initial_inventory
    outstanding_orders = config1.outstanding_orders
    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    hospital = Hospital(item_ids,
                        ordering_policies,
                        item_delivery_times,
                        {},
                        initial_inventory,
                        outstanding_orders,
                        surgeries=config1.surgeries)
    hospital.set_surgery_item_usage(config1.surgery_item_usage)
    hospital.set_surgery_stochastic_demand(config1.surgery_stochastic_demand)
    hospital.set_booked_surgery_stochastic_demand(config1.surgery_booked_demand)
    hospital.set_sim_time(simtime)
    # env.process(receive_order(env, hospital))
    # env.process(item_demand_from_surgeries(env, hospital))
    # env.process(book_surgeries(env, hospital))
    # env.process(place_order(env, ordering_policies, item_delivery_times, hospital))
    # env.process(hospital_bookkeeping(env, hospital))
    env.run(until=simtime)
    hospital.clean_data(warmup)
    if show:
        print("Average Inventory Level")
        for item_id in item_ids:
            print("{0}: {1}".format(item_id, str(np.mean(hospital.historical_inventory_levels[item_id]))))
        for item in hospital.stockouts:
            print("{0}: {1}".format(item, len(hospital.stockouts[item])))
        print(hospital.stockouts)
    return hospital


if __name__ == "__main__":

    if False:
        """ Item Driven Simulation test"""
        for k in [5, 10, 15]:
            for l in [2, 3, 4]:
                condoi_level = k
                lead_time = l
                demand = 1
                config = Item_Sim_Config(
                    item_ids=["item1"],
                    ordering_policies={"item1": DeterministicConDOIPolicyV2("item1", constant_days=condoi_level)},
                    item_delivery_times={"item1": GenerateDeterministic(lead_time)},
                    initial_inventory={"item1": 0},
                    outstanding_orders={"item1": set()},
                    item_stochastic_demands={"item1": GenerateDeterministic(demand)})
                print("=================== START REPORT===================")
                print("conDOI Level:", condoi_level)
                print("lead time:", lead_time)
                print("demand:", demand)
                run_item_driven_simulation(config, show=True)
                print("======================== END ========================")

    if False:
        """ Stochastic Surgery Driven Simulation test"""
        condoi_level = 5
        lead_time = 2
        config = Stochastic_Surgery_Config(
            item_ids=["item1"],
            surgeries=["surgery1", "surgery2", "surgery3"],
            ordering_policies={"item1": DeterministicConDOIPolicyV2("item1", constant_days=condoi_level)},
            item_delivery_times={"item1": GenerateDeterministic(lead_time)},
            initial_inventory={"item1": 0},
            outstanding_orders={"item1": set()},
            surgery_item_usage={"surgery1": {"item1": GenerateDeterministic(1)},
                                "surgery2": {"item1": GenerateDeterministic(2)},
                                "surgery3": {"item1": GenerateDeterministic(3)}
                                },
            surgery_stochastic_demand={"surgery1": GenerateDeterministic(3),
                                       "surgery2": GenerateDeterministic(2),
                                       "surgery3": GenerateDeterministic(1)
                                       },
            item_stochastic_demands={"item1": GenerateDeterministic(0)})
        print("=================== START REPORT===================")
        print("conDOI Level:", condoi_level)
        print("lead time:", lead_time)
        run_stochastic_surgery_driven_simulation(config, show=True)
        print("======================== END ========================")

    if True:
        """ Booked Surgery Driven Simulation test"""
        condoi_level = 5
        lead_time = 2
        config = Booked_Surgery_Config(
            item_ids=["item1"],
            surgeries=["surgery1", "surgery2", "surgery3"],
            ordering_policies={"item1": DeterministicConDOIPolicyV2("item1", constant_days=condoi_level)},
            item_delivery_times={"item1": GenerateDeterministic(lead_time)},
            initial_inventory={"item1": 0},
            outstanding_orders={"item1": set()},
            surgery_item_usage={"surgery1": {"item1": GenerateDeterministic(1)},
                                "surgery2": {"item1": GenerateDeterministic(2)},
                                "surgery3": {"item1": GenerateDeterministic(3)}
                                },
            surgery_stochastic_demand={"surgery1": GenerateDeterministic(3),
                                       "surgery2": GenerateDeterministic(2),
                                       "surgery3": GenerateDeterministic(1)
                                       },
            surgery_booked_demand={"surgery1": GenerateDeterministic(2),
                                   "surgery2": GenerateDeterministic(1),
                                   "surgery3": GenerateDeterministic(3)
                                   },
            item_stochastic_demands={"item1": GenerateDeterministic(0)})
        print("=================== START REPORT===================")
        print("conDOI Level:", condoi_level)
        print("lead time:", lead_time)
        run_booked_surgery_driven_simulation(config, show=True)
        print("======================== END ========================")
