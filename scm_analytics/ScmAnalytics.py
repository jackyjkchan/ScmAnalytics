import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from os import path
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
from scm_analytics.AnalyticsCore import AnalyticsCore
from scm_analytics.profiles.UsageProfile import UsageProfile
from scm_analytics.profiles.SurgeryProfile import SurgeryProfile
from scm_analytics.profiles.PoProfile import PoProfile
from scm_analytics.profiles.CaseCartProfile import CaseCartProfile

#from scm_analytics.profiles import SurgeryProfile, UsageProfile


class ScmAnalytics(AnalyticsCore):

    def __init__(self, configs):

        self.config = configs

        # deprecated, to be removed
        data_model_path = configs.data_model_path
        po_df = pd.read_pickle(path.join(data_model_path, "po_df"))
        usage_df = pd.read_pickle(path.join(data_model_path, "usage_df"))
        case_cart_df = pd.read_pickle(path.join(data_model_path, "case_cart_df"))
        self.item_catalog_df = pd.read_pickle(path.join(data_model_path, "item_catalog_df"))
        surgery_df = pd.read_pickle(path.join(data_model_path, "surgery_df"))

        # new way of storing dfs
        self.usage = UsageProfile(usage_df)
        self.surgery = SurgeryProfile(surgery_df)
        self.po = PoProfile(po_df)
        self.case_cart = CaseCartProfile(case_cart_df)

    def classify_items(self, exp_boundary=[0, 80, 95, 101], vol_boundary=None):
        po_df = self.po_df
        po_df = po_df[po_df["qty"] > 0]
        po_df["total_expenditure"] = po_df["qty"] * po_df["unit_price"]
        po_df["ea_price"] = po_df["total_expenditure"] / po_df["qty_ea"]
        item_ABC = po_df.groupby(["item_id"]).agg({
            'qty_ea': 'sum',
            'ea_price': 'mean',
            'total_expenditure': 'sum'
        }).reset_index()
        total_expense = sum(item_ABC["total_expenditure"])
        total_vol = sum(item_ABC["qty_ea"])
        item_ABC = item_ABC.sort_values(['ea_price'], ascending=[0])
        item_ABC["vol_percentage_cumsum"] = item_ABC["qty_ea"].cumsum() / total_vol * 100
        item_ABC["exp_percentage_cumsum"] = item_ABC["total_expenditure"].cumsum() / total_expense * 100

        if vol_boundary:
            item_ABC["abc_class"] = item_ABC["vol_percentage_cumsum"]\
                                        .apply(lambda x: sum([x > e for e in vol_boundary]))
        else:
            item_ABC["abc_class"] = item_ABC["exp_percentage_cumsum"] \
                .apply(lambda x: sum([x > e for e in exp_boundary]))
        self.item_catalog_df.join(item_ABC[["item_id", "abc_class"]].set_index(["item_id"]),
                                  on="item_id",
                                  how="left",
                                  rsuffix="abc")

        return item_ABC[["item_id", "abc_class", "total_expenditure", "qty_ea", "ea_price"]]

    def classify_usage_items(self, exp_boundary=[0, 60, 95, 101], vol_boundary=None):
        usage_df = self.usage.df
        catalog_df = self.item_catalog_df
        usage_df = usage_df[usage_df["code_name"] != "INSTRUMENTS REUSABLE"]
        usage_df["total_expenditure"] = usage_df["used_qty"] * usage_df["unit_price"]
        item_ABC = usage_df.groupby(["item_id"]).agg({
            'used_qty': 'sum',
            'total_expenditure': 'sum',
            'unit_price': 'mean',
            'code_name': 'max'
        }).reset_index()
        total_expense = sum(item_ABC["total_expenditure"])
        total_vol = sum(item_ABC["used_qty"])
        item_ABC = item_ABC.sort_values(['unit_price'], ascending=[0])
        item_ABC["vol_percentage_cumsum"] = item_ABC["used_qty"].cumsum() / total_vol * 100
        item_ABC["exp_percentage_cumsum"] = item_ABC["total_expenditure"].cumsum() / total_expense * 100

        if vol_boundary:
            item_ABC["abc_class"] = item_ABC["vol_percentage_cumsum"]\
                                        .apply(lambda x: sum([x > e for e in vol_boundary]))
        else:
            item_ABC["abc_class"] = item_ABC["exp_percentage_cumsum"] \
                .apply(lambda x: sum([x > e for e in exp_boundary]))
        self.item_catalog_df.join(item_ABC[["item_id", "abc_class"]].set_index(["item_id"]),
                                  on="item_id",
                                  how="left",
                                  rsuffix="abc")

        return item_ABC[["item_id", "code_name", "abc_class", "total_expenditure", "used_qty", "unit_price"]]

    def price_vs_vol_scatterplot(self, expense_cutoff=0.4):
        po_df = self.po_df
        po_df = po_df[po_df["qty"] > 0]
        po_df["total_expenditure"] = po_df["qty"] * po_df["unit_price"]
        po_df["ea_price"] = po_df["total_expenditure"] / po_df["qty_ea"]
        item_ABC = po_df.groupby(["item_id"]).agg({
            'qty_ea': 'sum',
            'ea_price': 'mean',
            'total_expenditure': 'sum'
        }).reset_index()
        total_expense = sum(item_ABC["total_expenditure"])
        total_vol = sum(item_ABC["qty_ea"])
        item_ABC = item_ABC.sort_values(['total_expenditure'], ascending=[0])
        item_ABC["vol_percentage_cumsum"] = item_ABC["qty_ea"].cumsum() / total_vol
        item_ABC["exp_percentage_cumsum"] = item_ABC["total_expenditure"].cumsum() / total_expense

        print(item_ABC[item_ABC["vol_percentage_cumsum"] < expense_cutoff][["item_id",
                                                                            "total_expenditure",
                                                                            "qty_ea",
                                                                            "ea_price"]])

        plt.scatter(range(0,len(item_ABC)),
                    item_ABC["exp_percentage_cumsum"],
                    s=1)
        plt.show()

    def process_surg_vectors(self, item_ids, normalized=False, filter_zeros=True):
        usage_df = self.usage.df
        surg_item_df = self.usage.df.groupby(["event_id"]).agg({
            'used_qty': 'sum'
        }).reset_index()
        surg_item_df = surg_item_df.rename(columns={'used_qty': 'total_items'})
        for item_id in item_ids:
            usage_lkup = usage_df[usage_df["item_id"] == item_id][["event_id", "used_qty"]]
            surg_item_df = surg_item_df.join(usage_lkup.set_index(["event_id"]),
                                             on="event_id",
                                             how="left",
                                             rsuffix="vect")
            surg_item_df = surg_item_df.rename(columns={'used_qty': item_id})
            surg_item_df = surg_item_df.fillna(0)

        surg_item_df["included_items"] = 0
        for item_id in item_ids:
            surg_item_df["included_items"] = surg_item_df["included_items"] + surg_item_df[item_id]
        surg_item_df = surg_item_df.sort_values(['included_items'], ascending=[0])

        if filter_zeros:
            surg_item_df = surg_item_df[surg_item_df['included_items'] > 0]

        if normalized:
            for item_id in item_ids:
                surg_item_df[item_id] = surg_item_df[item_id] / max(surg_item_df[item_id])

        print(surg_item_df)
        X = surg_item_df[item_ids]
        return X, surg_item_df

    def kcluster_elbow_plot(self, item_ids, K=30, label=None, show=True, normalized=False):
        X, surg_item_df = self.process_surg_vectors(item_ids, normalized=normalized)
        ks = range(1, K)

        distortions = []
        for k in ks:
            kmean_model = KMeans(n_clusters=k).fit(X)
            distortions.append(sum(np.min(cdist(X, kmean_model.cluster_centers_, 'euclidean'), axis=1)) / X.shape[0])

        plt.plot(ks, distortions,  marker="x", label=label)
        plt.xlabel('k')
        plt.ylabel('Distortion')
        plt.title('The Elbow Method showing the optimal k')
        if label:
            plt.legend()
        if show:
            plt.show()
        return

    def kcluster_surgeries(self, item_ids, k=12, normalized=False):
        X, surg_item_usage_df = self.process_surg_vectors(item_ids, normalized=normalized)
        kmean_model = KMeans(n_clusters=k, random_state=2345, max_iter=1000).fit(X)
        kmean_model.fit(X)
        labels = kmean_model.predict(X)
        surg_item_usage_df["kmean_label"] = labels
        surg_item_usage_df = surg_item_usage_df.join(
            self.surgery.df[["event_id", "scheduled_procedures", "case_service"]].set_index("event_id"),
            on="event_id",
            how="left",
            rsuffix="surgery")

        # build normalized item_usage_df for
        self.usage.df = self.usage.df.join(
            surg_item_usage_df[["event_id", "kmean_label"]].set_index("event_id"),
            on="event_id",
            how="left",
            rsuffix="cluster"
        )
        return surg_item_usage_df

    def analyze_item_usage_by_case_service(self):
        usage_df = self.usage.df
        po_df = self.po.df

        start = min(usage_df["start_dt"])
        end = max(usage_df["start_dt"])
        po_df = po_df[po_df["order_date"] >= start]
        po_df = po_df[po_df["order_date"] <= end]
        po_df["leadtime_intdays"] = po_df["order_leadtime"].apply(lambda x: x.days)

        usage_items = set(usage_df["item_id"])
        case_services = set(usage_df[usage_df["case_service"].notna()]["case_service"])
        po_items = set(po_df["item_id"])

        po_summary_df = po_df.groupby(["item_id"]).agg({
            'po_id': "nunique",
            'qty_ea': 'sum',
            'leadtime_intdays': ['mean', 'std']
        }).reset_index()

        po_summary_df.columns = [' '.join(col).strip().replace(" ", "_") for col in po_summary_df.columns.values]
        po_summary_df = po_summary_df.rename(columns={"qty_ea_sum": "ordered_qty",
                                                      "po_id_nunique": "orders_placed"})

        common_items = usage_items.intersection(po_items)
        usage_df = usage_df[usage_df["item_id"].isin(common_items)]

        item_used_lkup = usage_df.groupby(["item_id", "case_service"]).agg({"used_qty": "sum",
                                                                            "code_name": "max",
                                                                            "unit_price": "max"}).reset_index()

        item_used_df = item_used_lkup.pivot(index="item_id", columns="case_service", values='used_qty') \
            .fillna(0) \
            .reset_index()
        item_used_df["total_used_qty"] = item_used_df[[c for c in case_services]].sum(axis=1)
        for c in case_services:
            item_used_df[c] = item_used_df[c] / item_used_df["total_used_qty"]

        self.item_catalog_df = self.item_catalog_df.join(
            item_used_df[["item_id"]+list(case_services)+["total_used_qty"]].set_index("item_id"),
            on="item_id",
            how="left",
            rsuffix="case_service")

    def date_to_day_of_week(self, df, col):
        weekday_map = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday"
        }

        col = df[col].apply(lambda x:
                            weekday_map[x.weekday()]
                            if x.weekday() in weekday_map
                            else np.nan)
        return col

    def process_month_column(self):
        self.df['month'] = self.df['case_dt'].apply(lambda x: str(x.month))