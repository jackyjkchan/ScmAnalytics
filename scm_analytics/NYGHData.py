import pandas as pd
import os


class NYGHData:

    def __init__(self):
        self.local_src_path = 'C:\\Users\Jacky\Google Drive\MASc\workspace\inventory_supplychain_model\srcData\\NYGH'
        self.local_cache_path = 'C:\\Users\Jacky\Google Drive\MASc\workspace\inventory_supplychain_model\\cache'


        # historical_surgery
        # SchEventId, CaseDate, BookingDtTm, CASE_CART_ID, UrgentVsElective
        # S_StrategicProjLHSCSP-0081-00 Supply Chain Transform2 CPIO ProjectUofT ProjectDataSent to U of T October 26th, 20181. Historical Data for Surgeries

        # case_carts
        # pick lists in our terminology, picklist to LHSC seems to map to our preference list
        # case_cart_id, SchEventId, item_id, FILL_QTY, OPEN_QTY, HOLD_QTY
        # S_StrategicProjLHSCSP-0081-00 Supply Chain Transform2 CPIO ProjectUofT ProjectDataSent to U of T October 26th, 20182.Case Carts Used

        # procurement PO
        # PO_NO, PO_DATE, ITEM_NO (item_id), QTY, UM_CD (unit, ea, bx, bg), UNIT PRICE, LAST_RCV_DATE
        # S_StrategicProjLHSCSP-0081-00 Supply Chain Transform2 CPIO ProjectUofT ProjectDataSent to U of T October 26th, 20184.. UOT PO with Receipt Date and PO Class 5 YR

        # item catalog
        # Item_No, Unit of Measure1, Price 1, Qty 1, Unit of Measure 2, Price 2, Stock Or Non Stock
        # S_StrategicProjLHSCSP-0081-00 Supply Chain Transform2 CPIO ProjectUofT ProjectDataSent to U of T October 26th, 20186. UOT HMMS_Item_Master_Catalog_V5 20180615 with pricing

        # orange bag project aka Usage data
        # SchEventId, Item_Number, exp_code_name, Requisition_Qty, wastage qty
        #

        self.historical_surgery_dir = "surgery"


        self.case_carts_fn = "S_StrategicProjLHSCSP-0081-00 Supply Chain Transform2 CPIO ProjectUofT ProjectDataSent to U of T October 26th, 20182.Case Carts Used"
        self.procurement_fn = "S_StrategicProjLHSCSP-0081-00 Supply Chain Transform2 CPIO ProjectUofT ProjectDataSent to U of T October 26th, 20184.. UOT PO with Receipt Date and PO Class 5 YR"
        self.item_catalog_fn = "S_StrategicProjLHSCSP-0081-00 Supply Chain Transform2 CPIO ProjectUofT ProjectDataSent to U of T October 26th, 20186. UOT HMMS_Item_Master_Catalog_V5 20180615 with pricing"
        self.usage_fn = "S_StrategicProjLHSCSP-0081-00 Supply Chain Transform2 CPIO ProjectUofT ProjectDataSent to U of T October 26th, 20183._Consumable items (Orange Bag)"

        self.local_historical_surgery_fn = "LHS_surgery_history_v2.xlsx"
        self.local_case_cart_fn = "LHS_case_cart_v2.csv"
        self.local_procurement_fn = "LHS_PO.xlsx"
        self.local_hmms_procurement_fn = "LHS_HMMS_PO.xlsx"
        self.local_item_catalog_fn = "LHS_item_catalog.xlsx"
        self.local_usage_fn = "LHS_usage.xlsx"

        self.po_df = pd.DataFrame()
        self.hmms_po_df = pd.DataFrame()
        self.surgery_df = pd.DataFrame()
        self.case_cart_df = pd.DataFrame()
        self.usage_df = pd.DataFrame()
        self.item_catalog_df = pd.DataFrame()


    def load_po(self):
        self.po_df = pd.read_excel(os.path.join(self.local_src_path, self.local_procurement_fn))
        self.hmms_po_df = pd.read_excel(os.path.join(self.local_src_path, self.local_hmms_procurement_fn))
        #self.po_df["PO_DATE2"] = pd.to_datetime(self.po_df["PO_DATE"])

    def load_surgery(self):
        surgery_df = pd.DataFrame()
        for f in os.listdir(os.path.join(self.local_src_path, self.historical_surgery_dir)):
            self.surgery_df = pd.read_excel(os.path.join(self.local_src_path, self.local_historical_surgery_fn))

    def load_case_cart(self):
        self.case_cart_df = pd.read_csv(os.path.join(self.local_src_path, self.local_case_cart_fn))

    def load_item_catalog(self):
        self.item_catalog_df = pd.read_excel(os.path.join(self.local_src_path, self.local_item_catalog_fn))

    def load_usage(self):
        self.usage_df = pd.read_excel(os.path.join(self.local_src_path, self.local_usage_fn))

    def cache_all(self):
        self.po_df.to_pickle(os.path.join(self.local_cache_path, "po_df"))
        self.hmms_po_df.to_pickle(os.path.join(self.local_cache_path, "hmms_po_df"))
        self.surgery_df.to_pickle(os.path.join(self.local_cache_path, "surgery_df"))
        self.case_cart_df.to_pickle(os.path.join(self.local_cache_path, "case_cart_df"))
        #self.usage_df.to_pickle(os.path.join(self.local_cache_path, "usage_df"))
        #self.item_catalog_df.to_pickle(os.path.join(self.local_cache_path, "item_catalog_df"))

    def load_cache(self):
        self.po_df = pd.read_pickle(os.path.join(self.local_cache_path, "po_df"))
        self.surgery_df = pd.read_pickle(os.path.join(self.local_cache_path, "surgery_df"))
        self.case_cart_df = pd.read_pickle(os.path.join(self.local_cache_path, "case_cart_df"))
        self.usage_df = pd.read_pickle(os.path.join(self.local_cache_path, "usage_df"))
        self.item_catalog_df = pd.read_pickle(os.path.join(self.local_cache_path, "item_catalog_df"))

    def format_data(self):
        self.po_df["PO_DATE"] = pd.to_datetime(self.po_df["PO_DATE"])
        self.po_df["LAST_RCV_DATE"] = pd.to_datetime(self.po_df["LAST_RCV_DATE"])
        self.po_df["PO_NO"] = self.po_df["PO_NO"].astype(str)
        self.po_df = self.po_df[self.po_df["QTY"].notna()]
        self.po_df = self.po_df[self.po_df["UNIT PRICE"].notna()]


#nygh = NYGHData()
local_src_path = 'C:\\Users\Jacky\Google Drive\MASc\workspace\inventory_supplychain_model\srcData\\NYGH'
historical_surgery_dir = "surgery_updated"
surgery_df = pd.DataFrame()
for f in os.listdir(os.path.join(local_src_path, historical_surgery_dir)):

    df = pd.read_csv(os.path.join(local_src_path, historical_surgery_dir, f), encoding="ansi")
    surgery_df = pd.concat([surgery_df, df])

surgery_df["PREF_CARD_ID"] = surgery_df["PREF_CARD_ID"].apply(lambda x: str(x))
surgery_df["CASE_START_DATE_TIME"] = pd.to_datetime(surgery_df["CASE_START_DATE_TIME"])











#
# preference_card_dir = "preference_cards"
# preference_card_df = pd.DataFrame()
# for f in os.listdir(os.path.join(local_src_path, preference_card_dir)):
#
#     df = pd.read_csv(os.path.join(local_src_path, preference_card_dir, f), encoding="ansi")
#     preference_card_df = pd.concat([preference_card_df, df])
#
# preference_card_df["PREF_CARD_ID"] = preference_card_df["PREF_CARD_ID"].apply(lambda x: str(round(x)))
#
# surgery_pref_cards = set(surgery_df["Preference Card ID"])
# pref_cards = set(preference_card_df["PREF_CARD_ID"])
#
# print(len(surgery_pref_cards - pref_cards))
# print(len(surgery_pref_cards.intersection(pref_cards)))
#
# start = pd.Timestamp(2013, 1, 1)
# end = pd.Timestamp(2014, 1, 1)
# df = surgery_df[surgery_df["Case Start Date/Time"] > start]
# df = df[df["Case Start Date/Time"] < end]
#
#
# surgery_pref_cards = set(df["Preference Card ID"])
# pref_cards = set(preference_card_df["PREF_CARD_ID"])
# print(len(surgery_pref_cards - pref_cards))
# print(len(surgery_pref_cards.intersection(pref_cards)))