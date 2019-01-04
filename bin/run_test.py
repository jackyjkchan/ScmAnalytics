import bin.LHS_cluster_item_usage_metric as LHS_cluster_item_usage_metric
import bin.LHS_surgery_clustering_elbow_plot as LHS_surgery_clustering_elbow_plot
import bin.LHS_surgery_clustering_custom_plots as LHS_surgery_clustering_custom_plots

if __name__ == "__main__":
    assert (LHS_cluster_item_usage_metric.main() == 0)

    assert (LHS_surgery_clustering_elbow_plot.main() == 0)

    assert (LHS_surgery_clustering_custom_plots.main() == 0)

