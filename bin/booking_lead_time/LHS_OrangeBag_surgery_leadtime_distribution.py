from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.UsageMetrics import BookingLeadTimeDistribution
from os import path

if __name__ == "__main__":
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    for pattern in ["hernia.*repair"]:
        surgery_filter = {"dim": "scheduled_procedures",
                          "op": "re",
                          "val": pattern}
        urgent_filter = {"dim": "urgent_elective",
                          "op": "eq",
                          "val": "Urgent"}
        filters = [surgery_filter, urgent_filter]

        for x_units in ["days", "1hours", "weeks", "halfhours"]:
            title = "Booking Lead Time Distribution for [{0}] Surgeries ({1} Bins)" \
                .format(analytics.filter_desc(filters), x_units)
            x_label = "{0} Bins".format(x_units)
            y_label = "Surgery Count"

            data = BookingLeadTimeDistribution() \
                .set_x_units(x_units) \
                .get_data(analytics.usage.df, filters=filters)
            analytics.time_distribution_plt(data,
                                            x_units,
                                            save_dir=path.join(config.LHS().results_path, "test"),
                                            title=title,
                                            x_label=x_label,
                                            y_label=y_label,
                                            show=False)

