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


if __name__ == '__main__':
    levels = [1, 1.25, 1.5, 1.75, 2, 2.33, 2.66, 3, 3.5, 4, 5, 6, 9]
    levels = [6, 6.25, 6.5, 6.75, 7, 7.25, 7.5, 7.75, 8]
    trials = 50

    random.seed(0)
    pool = Pool(processes=10)
    seeds = random.randint(0, 9999999, trials)

    urgent_ratios = [0.1, 0.25, 0.5, 0.75, 1]
    urgent_ratio = 0.2
    betas = [1, 0.9, 0.8, 0.7, 0.5]
    betas = [0.7]
    policy_names = list("PoutWithScheduleBeta{0}".format(str(beta)) for beta in betas)
    lead_times = {"LT_Uni_3_4_5": GenerateFromSample([3, 4, 5])}

    base_dir = "results_fine_pout_20180418"
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())
    for lead_time_config in lead_times:
        lead_time_rng = lead_times[lead_time_config]

        average_stockout_rate = {policy: [] for policy in policy_names}

        stockout_rate_CI = {policy: [] for policy in policy_names}

        average_inventory = {policy: [] for policy in policy_names}

        for conD_lvl in levels:
            item_id = "item1"
            policies = {"PoutWithScheduleBeta{0}".format(str(beta)): POUTPolicy(item_id, beta, conD_lvl * 8)
                        for beta in betas}

            for policy in policies:
                start_time = datetime.datetime.now()

                results_dir = path.join(base_dir,
                                        "{0}_lvl={1}_urgent_rate={2}_{3}".format(policy,
                                                                                 conD_lvl,
                                                                                 urgent_ratio,
                                                                                 lead_time_config))

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
                hospitals = list(create_hospital(sim_config, seed=seed) for seed in seeds)
                print("created hospitals:", hospitals)
                results = pool.map(run_pre_generated_hospital, hospitals)
                print("done sim")

                stock_out_rates = list(len(results[i].stockouts[item_id])/10000 for i in range(trials))
                inventory_levels = list(mean(results[i].historical_inventory_levels[item_id]) for i in range(trials))

                mean_rate = mean(stock_out_rates)
                average_stockout_rate[policy].append(mean_rate)
                stockout_rate_CI[policy].append(1.96*sqrt(mean_rate * (1 - mean_rate) / (trials*10000)))
                average_inventory[policy].append(mean(inventory_levels))

                if not path.exists(results_dir):
                    makedirs(results_dir)
                with open(path.join(results_dir, policy + "_summary.txt"), "a") as f:
                    f.write("\t".join(["trial", "average_inventory", "stock_out_rate\n"]))
                    for trial in range(trials):
                        f.write("\t".join([str(trial),
                                           str(inventory_levels[trial]),
                                           str(stock_out_rates[trial])]))
                        f.write("\n")

                end_time = datetime.datetime.now()
                print("sim time:", end_time - start_time)
                print("======================== END ========================")

        results_dir = path.join(base_dir, "SUMMARY_urgent_rate={0}".format(urgent_ratio))
        if not path.exists(results_dir):
            makedirs(results_dir)

        plt.figure(figsize=(16, 8))
        for policy in policies:
            plt.errorbar(average_inventory[policy],
                         average_stockout_rate[policy],
                         fmt="x-",
                         yerr=stockout_rate_CI[policy],
                         label=policy)

        plt.title("Stockouts (std) vs Inventory Level urgent ratio = {0} {1} trials=10 sim=10k days".format(
            urgent_ratio,
            lead_time_config))
        plt.xlabel("Average Inventory Level")
        plt.ylabel("Stock out rate")
        plt.legend()
        plt.savefig(path.join(results_dir, "policy_comparison_{0}.svg".format(lead_time_config)),
                    format='svg',
                    orientation='landscape',
                    papertype='letter')
        plt.close()


















