class BaseProfile:

    def __init__(self, df):
        self.df = df
        self.mandatory_columns = []
        self.additional_columns = []

    def assert_structure(self):
        for col in self.mandatory_columns:
            assert(col in self.df)

