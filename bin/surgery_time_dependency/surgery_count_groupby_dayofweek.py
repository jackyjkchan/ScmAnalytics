from scm_analytics import ScmAnalytics, config
from scm_analytics.metrics.SurgeryMetrics import SurgeryCount, SurgeryHours
from os import path

if __name__ == "__main__":
    analytics = ScmAnalytics.ScmAnalytics(config.LHS())
    analytics.surgery.process_day_of_week_column()
    analytics.surgery.process_month_column()
    analytics.surgery.process_surgery_duration()

    elective_filter = {"dim": "urgent_elective",
                      "op": "eq",
                      "val": "Elective"}
    urgent_filter = {"dim": "urgent_elective",
                      "op": "eq",
                      "val": "Urgent"}

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Unknown"]
    month_order = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "nan"]

    # Surgery Count by Day of Week
    # analytics.metrics_barchart(analytics.surgery.df,
    #                            SurgeryCount(),
    #                            "day_of_week",
    #                            order=day_order,
    #                            save_dir=path.join(config.LHS().results_path, "test"),
    #                            show=True
    #                            )
    #
    # analytics.metrics_barchart(analytics.surgery.df,
    #                            SurgeryCount(),
    #                            "day_of_week",
    #                            order=day_order,
    #                            filters=[elective_filter],
    #                            save_dir=path.join(config.LHS().results_path, "test"),
    #                            show=True
    #                            )
    #
    # analytics.metrics_barchart(analytics.surgery.df,
    #                            SurgeryCount(),
    #                            "day_of_week",
    #                            order=day_order,
    #                            filters=[urgent_filter],
    #                            save_dir=path.join(config.LHS().results_path, "test"),
    #                            show=True
    #                            )

    #Surgery hours by days of week
    analytics.metrics_barchart(analytics.surgery.df,
                               SurgeryHours(),
                               "day_of_week",
                               order=day_order,
                               save_dir=path.join(config.LHS().results_path, "test"),
                               show=True
                               )

    analytics.metrics_barchart(analytics.surgery.df,
                               SurgeryHours(),
                               "day_of_week",
                               order=day_order,
                               filters=[elective_filter],
                               save_dir=path.join(config.LHS().results_path, "test"),
                               show=True
                               )

    analytics.metrics_barchart(analytics.surgery.df,
                               SurgeryHours(),
                               "day_of_week",
                               order=day_order,
                               filters=[urgent_filter],
                               save_dir=path.join(config.LHS().results_path, "test"),
                               show=True
                               )
    # Month
    analytics.metrics_barchart(analytics.surgery.df,
                               SurgeryCount(),
                               "month",
                               order=month_order,
                               save_dir=path.join(config.LHS().results_path, "test"),
                               show=True
                               )

    analytics.metrics_barchart(analytics.surgery.df,
                               SurgeryCount(),
                               "month",
                               order=month_order,
                               filters=[elective_filter],
                               save_dir=path.join(config.LHS().results_path, "test"),
                               show=True
                               )

    analytics.metrics_barchart(analytics.surgery.df,
                               SurgeryCount(),
                               "month",
                               order=month_order,
                               filters=[urgent_filter],
                               save_dir=path.join(config.LHS().results_path, "test"),
                               show=True
                               )
