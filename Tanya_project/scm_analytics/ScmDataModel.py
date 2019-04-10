import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from os import path


class ScmDataModel:

    def __init__(self, configs):
        data_model_path = configs.data_model_path
        self.po_df = pd.read_pickle(path.join(data_model_path, "po_df"))
        self.usage_df = pd.read_pickle(path.join(data_model_path, "usage_df"))
        self.case_cart_df = pd.read_pickle(path.join(data_model_path, "case_cart_df"))
        self.item_catalog_df = pd.read_pickle(path.join(data_model_path, "item_catalog_df"))
        self.surgery_df = pd.read_pickle(path.join(data_model_path, "surgery_df"))
