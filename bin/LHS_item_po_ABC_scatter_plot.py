from scm_analytics import ScmAnalytics, config
import matplotlib.pyplot as plt
import pandas as pd


if __name__ == "__main__":

    analytics = ScmAnalytics.ScmAnalytics(config.LHS())

    analytics.price_vs_vol_scatterplot()


    # po_df = analytics.po_df
    # print(po_df.iloc[4])
    # #po_df = po_df[po_df["unit_of_measure"] == "EA"]
    # po_df = po_df[po_df["qty"] > 0]
    # po_df["total_expenditure"] = po_df["qty"] * po_df["unit_price"]
    # po_df["ea_price"] = po_df["total_expenditure"] / po_df["qty_ea"]
    #
    # data = po_df.groupby(["item_id"]).agg({
    #     'qty_ea': 'sum',
    #     'ea_price': 'mean',
    #     'total_expenditure': 'sum'
    # }).reset_index()
    #
    # print(data.sort_values(['ea_price'], ascending=[0]))
    # print(data.sort_values(['qty_ea'], ascending=[0]))
    # total_expense = sum(data["total_expenditure"])
    # total_vol = sum(data["qty_ea"])
    # x_vol_percent = data.sort_values(['ea_price'], ascending=[0])["qty_ea"].cumsum()/total_vol * 100
    # y_expense_percent = data.sort_values(['ea_price'], ascending=[0])["total_expenditure"].cumsum()/total_expense * 100
    # plt.plot(x_vol_percent, y_expense_percent)
    # #plt.scatter(data["qty_ea"], data["ea_price"], s=1)
    # plt.show()

