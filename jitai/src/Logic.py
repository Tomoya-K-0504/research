

class BaseLogic:
    def __init__(self, ema_list):
        self.ema_df = ema_df
        self.ema_quitted_df = ema_quitted_df


class Logic:
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, answer_df, interrupt_df, *args, **kwargs):
        # TODO 介入のロジックを考える

        # "眠い"が75を超えたら、気分転換に散歩はどうですかメッセージ
        times_answered = list(set(answer_df.index))
        if len(answer_df) >= 1 and answer_df[answer_df["question"] == "眠い"].loc[times_answered[-1], "answer"] > 75:
            message_label = "sleepy"

        # 3回以上"疲れた"が70を超えていたら、お疲れですかのメッセージ
        elif len(answer_df) >= 3 and sum(answer_df[answer_df["question"] == "疲れた"].loc[times_answered[-3:], "answer"] > 70) == 3:
            message_label = "fatigue"

        if "message_label" not in locals().keys():
            message_label = "none"

        return message_label
