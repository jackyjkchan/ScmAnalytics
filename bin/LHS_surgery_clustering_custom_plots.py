from scm_analytics import ScmAnalytics, config
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
import math
import seaborn as sns
from os import path

def case_service_distribution_per_cluster(surg_item_usage_df):
    matplotlib.rcParams.update({'font.size': 5})
    n_clusters = len(set(surg_item_usage_df["kmean_label"]))
    case_services = list(set(surg_item_usage_df["case_service"]))
    case_services.sort()
    f, axes = plt.subplots(math.ceil(n_clusters/3), 3, sharex='col', figsize=(24, 9))
    case_service_by_cluster_df = surg_item_usage_df.groupby(["kmean_label", "case_service"])\
        .agg({'event_id': 'nunique'})\
        .unstack(fill_value=0)\
        .stack()\
        .reset_index()
    for i in range(0, n_clusters):
        ax = axes[int(i/3)][i % 3]
        case_services_df = case_service_by_cluster_df[case_service_by_cluster_df["kmean_label"] == i]
        index = np.arange(len(case_services))
        ax.bar(index, case_services_df["event_id"],
                tick_label=list(case_services_df["case_service"]))
        ax.set_ylabel('Count', fontsize=5)
        ax.set_title('Cluster #' + str(i), fontsize=5)
        ax.tick_params(axis='x', rotation=90)
    plt.savefig(path.join(config.LHS().results_path, "caseService_distribution_by_kmeansCluster.svg"),
                format='svg',
                orientation='landscape',
                papertype='letter')
    plt.show()

def item_usage_distribution_per_cluster(surg_item_usage_df, item_ids):

    clusters = list(set(surg_item_usage_df["kmean_label"]))
    clusters.sort()
    for cluster in clusters:
        #f, axes = plt.subplots(math.ceil(len(item_ids) / 5), 5, figsize=(48, 18))
        f, axes = plt.subplots(math.ceil(len(item_ids) / 5), 5, figsize=(32, 12))
        i = 0
        for item_id in item_ids:
            ax = axes[int(i / 5)][i % 5]
            bins = range(0, 1 + int(max(surg_item_usage_df[item_id])))
            all_data = surg_item_usage_df[surg_item_usage_df[item_id] > 0][item_id]
            cluster_data = surg_item_usage_df[surg_item_usage_df["kmean_label"] == cluster][item_id]
            ax.xaxis.set_ticks(np.arange(0, max(surg_item_usage_df[item_id]), 1.0))
            ax.hist(all_data,
                    bins,
                    rwidth=0.98,
                    alpha=0.5,
                    label="ALL")
            ax.hist(cluster_data,
                    bins,
                    rwidth=0.98,
                    alpha=0.5,
                    label="Cluster " + str(cluster))
            ax.set_title("[usage dist|usage>0] item id " + str(item_id))
            ax.legend()
            i=i+1

        plt.savefig(path.join(config.LHS().results_path, "cluster_"+str(cluster)+"_itemDist.svg"),
                    format='svg',
                    orientation='landscape',
                    papertype='letter')
        plt.close(f)


def caseService_count_by_cluster(surg_item_usage_df):
    matplotlib.rcParams.update({'font.size': 5})
    n_clusters = len(set(surg_item_usage_df["kmean_label"]))
    case_services = list(set(surg_item_usage_df["case_service"]))
    case_services.sort()
    f, axes = plt.subplots(math.ceil(n_clusters/3), 3, sharex='col')
    case_service_by_cluster_df = surg_item_usage_df.groupby(["kmean_label", "case_service"])\
        .agg({'event_id': 'nunique'})\
        .unstack(fill_value=0)\
        .stack()\
        .reset_index()
    for i in range(0, n_clusters):
        ax = axes[int(i/3)][i % 3]
        case_services_df = case_service_by_cluster_df[case_service_by_cluster_df["kmean_label"] == i]
        index = np.arange(len(case_services))
        ax.bar(index, case_services_df["event_id"],
                tick_label=list(case_services_df["case_service"])
               )
        ax.set_ylabel('Count', fontsize=5)
        ax.set_title('Cluster #' + str(i), fontsize=5)
        ax.tick_params(axis='x', rotation=90)
    plt.savefig(path.join(config.LHS().results_path, "caseService_distribution_by_kmeansCluster.svg"),
                format='svg',
                orientation='landscape',
                papertype='letter')
    plt.show()


def main():
    num_clusters = 12
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())
    item_df = analytics.classify_usage_items()
    item_df = item_df[item_df["used_qty"] > 200]
    print(item_df)
    item_ids = list(item_df.head(15)["item_id"])

    surg_item_usage_df = analytics.kcluster_surgeries(item_ids, k=num_clusters)
    case_service_distribution_per_cluster(surg_item_usage_df)
    item_usage_distribution_per_cluster(surg_item_usage_df, item_ids)
    caseService_count_by_cluster(surg_item_usage_df)
    return 0


if __name__ == "__main__":
    main()
