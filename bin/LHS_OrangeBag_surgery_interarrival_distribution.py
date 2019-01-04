from scm_analytics import ScmAnalytics, config


if __name__ == "__main__":
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    for pattern in ["hernia.*repair"]:
        surgery_filter = {"dim": "scheduled_procedures",
                          "op": "re",
                          "val": pattern}

        for x_units in ["days", "4hours", "weeks", "1hours", "halfhours"]:
            analytics.usage.surgery_inter_arrival_distribution.set_x_units(x_units)
            analytics.distribution_plot(analytics.usage.df,
                                        analytics.usage.surgery_inter_arrival_distribution,
                                        filter_dict=surgery_filter,
                                        save_dir=config.LHS().results_path,
                                        show=False)
