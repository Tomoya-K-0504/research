from abc import ABC
from datetime import datetime, timedelta

import pandas as pd
from jitai.src.utils import set_hour_minute


class EventTemplate(ABC):
    def __init__(self, param, user_info, ema, logger):
        self.param = param
        self.ema = ema
        self.name = param["condition_name"]
        self.ema_content = param["ema_content"]
        self.user_info = user_info
        self.logger = logger
        self.exists = param["exists"]
        self.ema_time = self.param["ema_time"]  # param["ema_time]"の値はdict

    def _init_ema_content(self):
        if not self.ema_content == "none":
            self.threshold = self.param["threshold"]
            self.more_or_less = self.param["more_or_less"]

    def _init_ema_time(self):
        # 時間に関する設定
        if list(self.ema_time.keys())[0] == "set_time":
            from_ = datetime.strptime(self.ema_time["set_time"]["from"], "%H:%M")
            self.ema_from_ = set_hour_minute(datetime.today(), from_)
            to = datetime.strptime(self.ema_time["set_time"]["to"], "%H:%M")
            self.ema_to = set_hour_minute(datetime.today(), to)
        if list(self.ema_time.keys())[0] == "interval":
            t = datetime.strptime(self.ema_time["interval"]["value"], "%H:%M")
            self.ema_from_ = datetime.today() - timedelta(hours=t.hour, minutes=t.minute)
            self.ema_to = datetime.today()

    def _validate_params(self):
        # TODO 与えられたパラメータが適切でないときにエラーを返す
        # 例えば、こちらが想定するquestionの中に、self.ema_contentで指定された要素がない場合とか

        pass

    def _extract_about_time(self):
        self.ema = self.ema[(self.ema["end"] >= self.ema_from_) & (self.ema["end"] <= self.ema_to)]

    def _ema_content_not_none(self):
        # このメソッドはDAMSの項目のみ有効, それ以外の場合はoverrideすること
        content_df = self.ema[self.ema["question"] == self.ema_content]
        content_df = content_df.astype({"answer": int})
        if not content_df.empty:
            if self.more_or_less == "more":
                self.ema = content_df[content_df["answer"] >= self.threshold]
            elif self.more_or_less == "less":
                self.ema = content_df[content_df["answer"] < self.threshold]
        else:
            self.ema = pd.DataFrame(columns=self.ema)

    def get_depend_class_last_ema_time(self):

        # TODO 要テスト. use=Falseに対して、これで本当にロジックが通るのか.
        if hasattr(self.depend_class, "use"):
            res = self.depend_class.ema.run()

        depend_ema = self.depend_class.ema

        if depend_ema.empty:
            self.ema = pd.DataFrame()
            return 0

        depend_ema.reset_index(drop=True, inplace=True)
        return depend_ema.loc[depend_ema.shape[0] - 1, "end"]

    def _depend_condition(self):
        # 従属関係の条件はここに記述する.
        self.ema_from_ = self.get_depend_class_last_ema_time()

        t = datetime.strptime(self.param["ema_time"]["interval"]["value"], "%H:%M")
        if self.ema_from_ != 0 and datetime.today() >= self.ema_from_ + timedelta(hours=t.hour, minutes=t.minute):
            return True
        else:
            return False

    def _run(self):
        if not self.ema.empty:
            self._extract_about_time()

        if not self.ema.empty and not self.ema_content == "none":
            self._ema_content_not_none()

    def run(self):

        if hasattr(self, "depend_class"):
            fill_cond_flag = self._depend_condition()
            # 〇〇時間経っていない場合にFalseが返る
            if not fill_cond_flag:
                return False

        self._run()
        if self.exists:
            return True if not self.ema.empty else False
        else:
            return True if self.ema.empty else False

    def add_depend_class(self, depend_class):
        self.depend_class = depend_class

    def copy(self):
        return EventTemplate(self.param, self.user_info, self.ema, self.logger)
