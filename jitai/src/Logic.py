from datetime import *
import jpholiday
from jitai.src.JmaScraper import JmaScraper


class BaseLogic:
    def __init__(self, ema_list):
        self.ema_df = ema_df
        self.ema_quitted_df = ema_quitted_df


class Logic:
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, answer_df, interrupt_df, *args, **kwargs):
        # TODO 介入のロジックを考える

        # 土日かつ天気がいい場合、お出かけしましょうのメッセージ
        today = datetime.today()
        today_weather_df = JmaScraper("大阪府", year=today.year, month=today.month, day=today.day).scrape()
        _ = today_weather_df[today_weather_df["day"].astype(int) == today.day-2]["weather_noon"].values[0]
        if (datetime.weekday(today) >= 4 or jpholiday.is_holiday_name(today.date())) and "晴" in today_weather_df[today_weather_df["day"].astype(int) == today.day-2]["weather_noon"].values[0]:
            return "off_day_go_outside"

        # "眠い"が75を超えたら、気分転換に散歩はどうですかメッセージ
        times_answered = list(set(answer_df.index))
        if len(answer_df) >= 1 and answer_df[answer_df["question"] == "眠い"].loc[times_answered[-1], "answer"] > 75:
            return "sleepy"

        # 3回以上"疲れた"が70を超えていたら、お疲れですかのメッセージ
        elif len(answer_df) >= 3 and sum(answer_df[answer_df["question"] == "疲れた"].loc[times_answered[-3:], "answer"] > 70) == 3:
            return "fatigue"

        else:
            return "none"




