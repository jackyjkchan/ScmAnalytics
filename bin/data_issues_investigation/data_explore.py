from scm_analytics import ScmAnalytics, config
import re
import pandas as pd
import numpy as np
from os import path
import random

random.seed(0)

cache_path = 'C:\\Users\Jacky\Google Drive\MASc\workspace\inventory_supplychain_model\cache'
local_cache_path = path.join(cache_path, "lhs_raw")
dump_data_model_path = path.join(cache_path, "lhs_data_model")

po_df = pd.read_pickle(path.join(local_cache_path, "po_df"))
surgery_df = pd.read_pickle(path.join(local_cache_path, "surgery_df"))
case_cart_df = pd.read_pickle(path.join(local_cache_path, "case_cart_df"))
usage_df = pd.read_pickle(path.join(local_cache_path, "usage_df"))
item_catalog_df = pd.read_pickle(path.join(local_cache_path, "item_catalog_df"))

po_df["PO_DATE"] = pd.to_datetime(po_df["PO_DATE"])
po_df["LAST_RCV_DATE"] = pd.to_datetime(po_df["LAST_RCV_DATE"])
po_df["PO_NO"] = po_df["PO_NO"].astype(str)
po_df = po_df[po_df["QTY"].notna()]
po_df = po_df[po_df["UNIT PRICE"].notna()]

po_rename = {
    "PO_NO":            "po_id",
    "PO_DATE":          "order_date",
    "PO_CLASS_CD":      "po_class",
    "ITEM_NO":          "item_id",
    "QTY":              "qty",
    "UM_CD":            "unit_of_measure",
    "UNIT PRICE":       "unit_price",
    "LAST_RCV_DATE":    "delivery_date",
    "QTY_RCV_TO_DATE":  "qty_received"
}
po_df = po_df.rename(columns=po_rename)

surgery_rename = {
    "SchEventId":                           "event_id",
    "AllScheduledProcedures":               "scheduled_procedures",
    "AllProcedures":                        "completed_procedures",
    "CaseService":                          "case_service",
    "Cancellation/DelayDueToSupplyIssue":   "supply_issue_desc",
    "ORDelayDesc":                          "OR_delay_desc",
    "ProcedureStartDtTm":                   "start_dt",
    "ProcedureStopDtTm":                    "end_dt",
    "CaseDate":                             "case_dt",
    "BookingDtTm":                          "booking_dt",
    "CASE_CART_ID":                         "case_cart_id",
    "UrgentVsElective":                     "urgent_elective"
}
surgery_df = surgery_df.rename(columns=surgery_rename)
surgery_df["event_id"] = surgery_df["event_id"].values.astype(np.int64).astype(str)

case_cart_rename = {
    "SchEventId":   "event_id",
    "Item_id":      "item_id",
    "FILL_QTY":     "fill_qty",
    "OPEN_QTY":     "open_qty",
    "HOLD_QTY":     "hold_qty"
}
case_cart_df = case_cart_df.rename(columns=case_cart_rename)
case_cart_df["event_id"] = case_cart_df["event_id"].values.astype(str)
case_cart_df["item_id"] = case_cart_df["item_id"].values.astype(str)
case_cart_df["case_cart_id"] = case_cart_df["case_cart_id"].values.astype(str)

usage_rename = {
    "SchEventId":       "event_id",
    "Item_Number":      "item_id",
    "exp_code_name":    "code_name",
    "Requisition_Qty":  "used_qty"
}
usage_df = usage_df.rename(columns=usage_rename)
usage_df["event_id"] = usage_df["event_id"].values.astype(str)
usage_df["item_id"] = usage_df["item_id"].values.astype(str)

item_cataog_rename = {
    "Item_No":                              "item_id",
    "Surginet Flag (interface to Cerner)":  "surginet_flag",
    "Unit Of Measure 1":                    "unit1",
    "Price 1":                              "price1",
    "Qty 1":                                "qty1",
    "Unit Of Measure 2":                    "unit2",
    "Price 2":                              "price2",
    "Qty 2":                                "qty2",
    "Unit Of Measure 3":                    "unit3",
    "Price 3":                              "price3",
    "Qty 3":                                "qty3",
    "Unit of Measure 4":                    "unit4",
    "Price 4":                              "price4",
    "Qty 4" :                               "qty4",
    "Unit of Measure 5":                    "unit5",
    "Price 5":                              "price5",
    "Stock Or Non Stock":                   "stock_nonstock"
}
item_catalog_df = item_catalog_df.rename(columns=item_cataog_rename)
item_catalog_df["item_id"] = item_catalog_df["item_id"].values.astype(str)

numeric_case_cart_items = set(case_cart_df[case_cart_df["item_id"].apply(lambda x: not bool(re.search("[a-zA-Z~]", str(x).lower())))]["item_id"])
numeric_usage_items = set(usage_df[usage_df["item_id"].apply(lambda x: not bool(re.search("[a-zA-Z~]", str(x).lower())))]["item_id"])
numeric_po_items = set(po_df[po_df["item_id"].apply(lambda x: not bool(re.search("[a-zA-Z~]", str(x).lower())))]["item_id"])

print("numeric items_numbers in case_cart:", len(numeric_case_cart_items))
print("numeric items_numbers in orange bag:", len(numeric_usage_items))
print("numeric items_numbers in po:", len(numeric_po_items))

print("\nnumber of usage items missing from po", len(numeric_usage_items-numeric_po_items))
print("Example of items:")
for i in range(0, 10):
    print(random.choice(list(numeric_usage_items-numeric_po_items)))

print("\nnumber of usage items missing from case_cart", len(numeric_usage_items-numeric_case_cart_items))
print("Example of items:")
for i in range(0, 10):
    print(random.choice(list(numeric_usage_items-numeric_case_cart_items)))

print("\nnumber of numeric case_cart items missing from usage", len(numeric_case_cart_items-numeric_usage_items))
print("Example of items:")
for i in range(0, 10):
    print(random.choice(list(numeric_case_cart_items-numeric_usage_items)))

case_cart_schEventIDs = set(case_cart_df["event_id"])
surgery_schEventIDs = set(surgery_df["event_id"])
usage_schEventIDs = set(usage_df["event_id"])

print("unique number of schEventIds in case_cart:", len(case_cart_schEventIDs))
print("unique number of schEventIds in surgeries:", len(surgery_schEventIDs))
print("unique number of schEventIds in orange bag:", len(usage_schEventIDs))

print("orange bag schEventIDs missing from case_cart:", len(usage_schEventIDs - case_cart_schEventIDs))

case_cart_df = case_cart_df.join(surgery_df[["event_id", "start_dt"]].set_index(["event_id"]),
                                 how="left",
                                 on=["event_id"],
                                 rsuffix="surgery")

usage_df = usage_df.join(surgery_df[["event_id", "start_dt"]].set_index(["event_id"]),
                                 how="left",
                                 on=["event_id"],
                                 rsuffix="surgery")

print("PO order date ranges:", min(po_df["order_date"]), max(po_df["order_date"]))
print("Surgery ProcedureStartDtTm ranges:", min(surgery_df["start_dt"]), max(surgery_df["start_dt"]))
print("case_cart date ranges:", min(case_cart_df["start_dt"]), max(case_cart_df["start_dt"]))
print("OrangeBag date ranges:", min(usage_df["start_dt"]), max(usage_df["start_dt"]))



surgeries_2013 = set(surgery_df[surgery_df["start_dt"] < "2014"]["event_id"])
case_carts_2013= set(case_cart_df[case_cart_df["start_dt"] < "2014"]["event_id"])
len(case_carts_2013)
len(surgeries_2013)

