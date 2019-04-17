from scm_analytics import ScmAnalytics, config

analytics = ScmAnalytics.ScmAnalytics(config.LHS())

po_df = analytics.po.df


item_id = "114970"
df = po_df[po_df["item_id"]==item_id]
df = df.sort_values(["order_date"])

order_deliveries = list(zip(df["order_date"], df["delivery_date"]))
cross_cnt = 0
for i in range(len(df)):
    print("{0}/{1}".format(str(i+1), str(len(df))))
    j = i+1
    while j < len(df) and order_deliveries[j][0] <= order_deliveries[i][0]:
        j += 1

    while j < len(df) and order_deliveries[j][0] < order_deliveries[i][1]:
        if order_deliveries[i][1] > order_deliveries[j][1]:
            cross_cnt += 1
            print(df.iloc[i])
        j += 1

print("item id: {0}".format(item_id))
print("crosses: {0}".format(str(cross_cnt)))
print("orders: {0}".format(str(len(df))))
print("cross %: {0}".format(str(cross_cnt/len(df))))
