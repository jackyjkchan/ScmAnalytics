from os import path
import numpy as np
import matplotlib.pyplot as plt
import re

class AnalyticsCore:

    def __init__(self, configs):
        self.results_path = configs.results_path

    def filter_desc(self, filter_dict):
        filter_val = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,*]", " ", str(filter_dict["val"]))
        return "{0} {1} {2}".format(filter_dict["dim"], filter_dict["op"], filter_val)

    def metrics_barchart(self, df, metric, groupby_dim, filter_dict=None, save_dir=None, show=False):
        data = metric.get_data(df, groupby_dim=groupby_dim, filter_dict=filter_dict)
        metric_name = metric.metric_name

        index = np.arange(len(set(data["x"])))
        plt.bar(index, data["y"],
                tick_label=data["x"]
                )
        plt.ylabel(metric_name)
        plt.xlabel(groupby_dim)
        title = metric_name + " grouped by " + groupby_dim
        if filter_dict:
            title = title + " [" + self.filter_desc(filter_dict) + "]"
        plt.title(title)
        if save_dir:
            plt.savefig(path.join(save_dir, title+".svg"),
                        format='svg',
                        orientation='landscape',
                        papertype='letter')
        if show:
            plt.show()
        plt.close()

    def distribution_plot(self, df, dist, filter_dict=None, save_dir=None, show=False):
        figsize = (15, 5)
        title = "{0} ({1})".format(dist.metric_name, dist.x_units)
        if filter_dict:
            title = title + " [" + self.filter_desc(filter_dict) + "]"

        args = {"x_unit": dist.x_units}
        bins = np.arange(0, 100, 25)
        interval = 1
        data = dist.get_data(df, filter_dict=filter_dict, args=args)
        if dist.x_units == "days":
            bins = np.arange(0, 30, 1)
            data = np.clip(data['y'], bins[0], bins[-1])
        elif dist.x_units == "weeks":
            bins = np.arange(0, 50, 1)
            data = np.clip(data['y'], bins[0], bins[-1])
        elif dist.x_units in ["4hours", "hours"]:
            interval = 4
            bins = np.arange(0, 5*24, interval)
            data = np.clip(data['y'], bins[0], bins[-1])
        elif dist.x_units == "1hours":
            interval = 1
            bins = np.arange(0, 48, interval)
            data = np.clip(data['y'], bins[0], bins[-1])
        elif dist.x_units == "halfhours":
            interval = 0.5
            bins = np.arange(0, 24, interval)
            data = np.clip(data['y'], bins[0], bins[-1])
            figsize = (20, 5)
        else:
            data = data['y']
            bins = None

        fig, ax = plt.subplots(figsize=figsize)
        _, bins, patches = plt.hist(data, bins=bins, rwidth=0.96)
        xlabels = bins[1:].astype(str)
        xlabels[-1] += '+'
        N_labels = len(xlabels)
        plt.xlim([bins[0], bins[-1]])
        plt.xticks(interval * np.arange(N_labels) + interval/2)
        ax.set_xticklabels(xlabels)

        plt.title(title)
        plt.ylabel(dist.y_label)
        plt.xlabel(dist.x_label)

        if save_dir:
            plt.savefig(path.join(save_dir, title+".svg"),
                        format='svg',
                        orientation='landscape',
                        papertype='letter')
        if show:
            plt.show()
        return
