from numpy import mean, std
import matplotlib.pyplot as plt
from os import path, makedirs

from rng_classes import GenerateFromSample, GenerateDeterministic, GenerateFromScaledLogNormal
from order_policies import POUTPolicy, POUTPolicyWithoutSchedule
from run_sim import run_pout_sim, Booked_Surgery_Config

from scm_analytics import ScmAnalytics
from scm_analytics import config as baseconfig

levels = [1, 2, 3, 5, 7, 10, 15, 20]

lead_times = {
    "LT_Uni_2_3_4": GenerateFromSample([2, 3, 4]),
    "LT_DiscreteD": GenerateFromSample(80*[2] + 5*[3] + 10*[4] + [5, 6, 7, 8, 9])}

base_dir = "results_20190409"

beta = 0.8

for urgent_ratio in [0.1, 0.25, 0.5, 0.75, 1]:
    for lead_time_config in lead_times:
        lead_time_rng = lead_times[lead_time_config]

        average_stockouts = {"WithSchedule": [],
                             "WithoutSchedules": []}
        std_stockouts = {"WithSchedule": [],
                         "WithoutSchedules": []}

        average_inventory = {"WithSchedule": [],
                             "WithoutSchedules": []}
        for out_lvl in levels:
            item_id = "item1"
            policies = {"WithSchedule": POUTPolicy(item_id, beta, out_lvl),
                        "WithoutSchedules": POUTPolicyWithoutSchedule(item_id, beta, out_lvl)}

            for policy in policies:
                results_dir = path.join(base_dir,
                                        "policy={0}_pout={1}_urgent_rate={2}_{3}".format(policy,
                                                                                         out_lvl,
                                                                                         urgent_ratio,
                                                                                         lead_time_config))

                if not path.exists(results_dir):
                    makedirs(results_dir)

                with open(path.join(results_dir, policy+"_summary.txt"), "a") as f:
                    f.write("\t".join(["trial", "average_inventory", "stockouts_per_10000\n"]))

                stockouts = []
                inventory_levels = []

                for trial in range(10):

                    surgeries = ["A"]
                    surgery_item_usage = {"A":  {item_id: GenerateDeterministic(1)}}
                    surgery_stochastic_demand = {"A": GenerateFromScaledLogNormal(2, 0.5, urgent_ratio)}
                    surgery_booked_demand = {"A": GenerateFromScaledLogNormal(2, 0.5, 1-urgent_ratio)}
                    item_delivery_times = {item_id: lead_time_rng}

                    config = Booked_Surgery_Config(
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

                    print("=================== START REPORT===================")
                    print("POUT Level:", out_lvl)
                    hospital = run_pout_sim(config, booking_lead_time=14, simtime=10500, show=True)
                    analytics = ScmAnalytics.ScmAnalytics(baseconfig.LHS())
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
                    f1, axes = plt.subplots(3, 1, figsize=(16, 15))
                    axes[0].hist(inventory, bins=range(0, int(max(inventory)+1)))
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
                                mean(hospital.historical_inventory_levels[item_id]) /
                                mean(hospital.historical_demand[item_id]))
                    axes[2].set_title(title)
                    axes[2].legend()

                    fn = "Inventory Trade Trial {0}".format(str(trial))
                    plt.savefig(path.join(results_dir, fn+".png"),
                                format='png',
                                orientation='landscape',
                                papertype='letter')
                    plt.close()
                    print("======================== END ========================")
                    with open(path.join(results_dir, policy + "_summary.txt"), "a") as f:
                        print(str(len(hospital.stockouts[item_id])))
                        f.write("\t".join([str(trial),
                                           str(mean(hospital.historical_inventory_levels[item_id])),
                                           str(len(hospital.stockouts[item_id]))]))
                        f.write("\n")
                    stockouts.append(len(hospital.stockouts[item_id]))
                    inventory_levels.append(mean(hospital.historical_inventory_levels[item_id]))

                average_stockouts[policy].append(mean(stockouts))
                std_stockouts[policy].append(std(stockouts))
                average_inventory[policy].append(mean(inventory_levels))

        results_dir = path.join(base_dir, "SUMMARY_urgent_rate={0}".format(urgent_ratio))
        if not path.exists(results_dir):
            makedirs(results_dir)

        plt.figure(figsize=(16, 8))
        plt.errorbar(average_inventory["WithSchedule"],
                     average_stockouts["WithSchedule"],
                     fmt="x-",
                     yerr=std_stockouts["WithSchedule"],
                     label="WithSchedule")
        plt.errorbar(average_inventory["WithoutSchedules"],
                     average_stockouts["WithoutSchedules"],
                     fmt="o-",
                     yerr=std_stockouts["WithoutSchedules"],
                     label="WithoutSchedules")
        plt.title("Stockouts (std) vs Inventory Level urgent ratio = {0} {1} trials=10 sim=10k days".format(
            urgent_ratio,
            lead_time_config))
        plt.xlabel("Average Inventory Level")
        plt.ylabel("stock outs in 10k days")
        plt.legend()
        plt.savefig(path.join(results_dir, "policy_comparison_{0}.svg".format(lead_time_config)),
                    format='svg',
                    orientation='landscape',
                    papertype='letter')
        plt.close()
