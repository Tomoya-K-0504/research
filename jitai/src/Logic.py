from datetime import *
import jpholiday
from jitai.src.JmaScraper import JmaScraper
from jitai.src.Dams import Dams


class BaseLogic:
    def __init__(self, ema_list):
        self.ema_df = ema_df
        self.ema_quitted_df = ema_quitted_df


class Logic:
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, answer_df, interrupt_df, *args, **kwargs):
        # TODO 介入のロジックを考える
        # TODO その人の平均値を閾値とする
        # TODO 1. DAMSの計算を入れる

        index_list = list(set(answer_df.index))

        # 土日かつ天気がいい場合、お出かけしましょうのメッセージ
        # today = datetime.today()
        # today_weather_df = JmaScraper("大阪府", year=today.year, month=today.month, day=today.day).scrape()
        # _ = today_weather_df[today_weather_df["day"].astype(int) == today.day-2]["weather_noon"].values[0]
        # if (datetime.weekday(today) >= 4 or jpholiday.is_holiday_name(today.date())) and "晴" in today_weather_df[today_weather_df["day"].astype(int) == today.day-2]["weather_noon"].values[0]:
        #     return "off_day_go_outside"

        # DAMSによる心理状態の把握
        answer_df["ema_id"] = answer_df.index
        answer_df.reset_index(inplace=True, drop=True)
        dams = Dams(answer_df[answer_df["ema_id"] == index_list[-1]])
        dams_thresh = 200

        # anxietyが200を超えると、「不安ですか？」
        if dams.anxiety >= dams_thresh:
            return "anxiety"

        # depressiveが200を超えると、「憂鬱ですか？」
        if dams.depressive >= dams_thresh:
            return "depressive"

        # positiveが200を超えると、「いい調子です！」
        if dams.positive >= dams_thresh:
            return "positive"

        # positiveが200を超えると、「気持ちが消極的ですか?」
        if dams.negative >= dams_thresh:
            return "negative"

        # "眠い"が75を超えたら、気分転換に散歩はどうですかメッセージ
        times_answered = list(set(answer_df.index))
        if len(answer_df) >= 1 and answer_df[answer_df["question"] == "眠い"].loc[times_answered[-1], "answer"] > 75:
            return "sleepy"

        # 3回以上"疲れた"が70を超えていたら、お疲れですかのメッセージ
        elif len(answer_df) >= 3 and sum(answer_df[answer_df["question"] == "疲れた"].loc[times_answered[-3:], "answer"] > 70) == 3:
            return "fatigue"

        else:
            return "none"




