from os import path

class LHS:

    def __init__(self):
        self.project_root = 'C:\\Users\Jacky\Google Drive\MASc\workspace\inventory_supplychain_model'
        self.cache_root = path.join(self.project_root, "cache")
        self.raw_path = path.join(self.cache_root, "lhs_raw")
        self.data_model_path = path.join(self.cache_root, "lhs_data_modelv2")
        self.results_path = path.join(self.project_root, "LHS_results")



