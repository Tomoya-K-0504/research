
positive_list = ["はつらつとした", "楽しい", "嬉しい"]
negative_list = ["暗い", "嫌な", "沈んだ"]
anxiety_list = ["気がかりな", "不安な", "心配な"]


class Dams:
    def __init__(self, ema_df):
        self.positive = 0
        self.negative = 0
        self.depressive = 0
        self.anxiety = 0
        self._calc_dams(ema_df)

    def _calc_dams(self, ema_df):
        self.positive = sum([ema_df.loc[ema_df["question"] == q, "answer"].values[0] for q in positive_list])
        self.negative = sum([ema_df.loc[ema_df["question"] == q, "answer"].values[0] for q in negative_list])
        self.anxiety = sum([ema_df.loc[ema_df["question"] == q, "answer"].values[0] for q in anxiety_list])
        self.depressive = self.negative + (300 - self.positive)



