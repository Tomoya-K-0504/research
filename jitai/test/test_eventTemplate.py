import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase

import pandas as pd
import copy
import yaml
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.events.EventTemplate import EventTemplate
from jitai.src.utils import set_hour_minute


class TestEventTemplate(TestCase):

    def setUp(self):
        """
        テストケース
          condition_name: sth
          event: [sleep or wake or nap or scheduled or default]
        """
        wake_test_case_dir = Path("testcases") / "mother_wake"
        self.ema = pd.read_csv(wake_test_case_dir / "model_test_case.csv", index_col=0)
        self.ema["end"] = pd.to_datetime(self.ema["end"])

        with open(const.PJ_ROOT / "yamls" / "test.yml") as f:
            self.params = yaml.load(f)

        self.user_info = const.USER_LIST.iloc[0]

        self.et = EventTemplate(
            self.params[0], user_info=self.user_info, ema=self.ema, logger=logger_file.logger(const.LOG_DIR))
        self.et = init_event_template(self.et)

    def test___init__(self):
        param_interval = self.params[0].copy()
        param_interval["ema_time"] = {"interval": {"value": "3:00"}}
        interval_ins = EventTemplate(param_interval, self.user_info, self.ema, logger_file.logger(const.LOG_DIR))
        interval_ins = init_event_template(interval_ins)
        self.assertEqual(interval_ins.ema_from_.hour, (datetime.today() - timedelta(hours=3)).hour)

    def test__extract_about_time(self):
        """
        # noneのとき、つまりEMAが選ぶ時間にあるかないかを見るとき
          ema_time: [set_time or interval]
            ema_time_values: ["from" and "to"] or interval_value
            exists: [true or false]
        """
        # EMAの日付をすべて今日にして、時間で切れるか確かめる. 18:00のデータが存在する.
        self.ema["end"] = self.ema["end"].map(lambda x: set_hour_minute(datetime.today(), x))
        # 昨日も含んでみる
        # self.ema.loc[:3, "end"] = self.ema.loc[:3, "end"] - timedelta(days=1)
        ema_from = set_hour_minute(datetime.today(), datetime.strptime("16:00", "%H:%M"))
        ema_to = set_hour_minute(datetime.today(), datetime.strptime("19:00", "%H:%M"))
        self.et.ema_from_ = ema_from
        self.et.ema_to = ema_to
        exists_ema = self.ema[(self.ema["end"] > ema_from) & (self.ema["end"] < ema_to)]
        nonexists_ema = self.ema[~((self.ema["end"] > ema_from) & (self.ema["end"] < ema_to))]

        self.et._extract_about_time()
        now = datetime.now()

        # 16:00~19:00以外にテストを実行するときのテストコード
        if now.hour < 16 or (now.hour == 19 and now.minute > 0) or now.hour > 19:
            self.assertEqual(self.et.ema.shape[0], exists_ema.shape[0])
            self.assertNotEqual(self.et.ema.shape[0], nonexists_ema.shape[0])

        # 18:03に実行するときのテストコード
        if now.hour == 18 and now.minute == 3:
            self.assertEqual(self.et.ema.shape[0], exists_ema.shape[0])
        # 16:00~19:00で18:03以外に実行するときのテストコード
        elif (16 <= now.hour <= 18) or (now.hour == 19 and now.minute == 0):
            self.assertEqual(self.et.ema.shape[0], 0)

    def test__ema_content_not_none(self):
        """
        ema_content: [none or はつらつとした or 楽しい or 嬉しい or 暗い or 嫌な or 沈んだ or 気がかりな or 不安な or 心配な]
          # noneでない、つまりEMAのある項目が閾値以上/未満を見るとき
          threshold: value
          more_or_less: [more or less]
        """
        # "暗い"に関するデータを抽出, パラメータをセット
        param_content = self.params[0].copy()
        param_content["ema_content"] = "暗い"
        darkness_df = self.ema[self.ema["question"] == "暗い"]
        darkness_df = darkness_df.astype({"answer": int})

        # "暗い"が80以上のデータを抽出
        param_content["threshold"] = 80
        param_content["more_or_less"] = "more"
        content_more_df = darkness_df[darkness_df["answer"] >= 80]
        content_more_ins = EventTemplate(
            param_content, user_info=self.user_info, ema=self.ema, logger=logger_file.logger(const.LOG_DIR))
        content_more_ins = init_event_template(content_more_ins)

        # "暗い"が20以下のデータを抽出
        param_content["threshold"] = 20
        param_content["more_or_less"] = "less"
        content_less_df = darkness_df[darkness_df["answer"] <= 20]
        content_less_ins = EventTemplate(
            param_content, user_info=self.user_info, ema=self.ema, logger=logger_file.logger(const.LOG_DIR))
        content_less_ins = init_event_template(content_less_ins)

        # "暗い"が10以下のデータはないので、空のdataframeを返す
        param_content["threshold"] = 10
        content_notexists_ins = EventTemplate(
            param_content, user_info=self.user_info, ema=self.ema, logger=logger_file.logger(const.LOG_DIR))
        content_notexists_ins = init_event_template(content_notexists_ins)

        # 更新を行う
        content_more_ins._ema_content_not_none()
        content_less_ins._ema_content_not_none()
        content_notexists_ins._ema_content_not_none()

        self.assertEqual(content_more_ins.ema.shape[0], content_more_df.shape[0])
        self.assertEqual(content_less_ins.ema.shape[0], content_less_df.shape[0])
        self.assertEqual(content_notexists_ins.ema.shape[0], pd.DataFrame().shape[0])

    def test__depend_condition(self):
        with open(const.PJ_ROOT / "yamls" / "depend_test.yml") as f:
            depend_params = yaml.load(f)
        param_depended = depend_params[0]
        param_depend = depend_params[1]

        depend_ins = EventTemplate(
            param_depend.copy(), user_info=self.user_info, ema=self.ema.copy(), logger=logger_file.logger(const.LOG_DIR))
        depend_ins = init_event_template(depend_ins)
        depend_nonexists_ins = EventTemplate(
            param_depend.copy(), user_info=self.user_info, ema=self.ema.copy(), logger=logger_file.logger(const.LOG_DIR))
        depend_nonexists_ins = init_event_template(depend_nonexists_ins)
        depended_ins = EventTemplate(
            depend_params[0].copy(), user_info=self.user_info, ema=self.ema, logger=logger_file.logger(const.LOG_DIR))
        depended_ins = init_event_template(depended_ins)
        depend_ins.add_depend_class(depended_ins)
        _ = depended_ins.copy()
        _ = init_event_template(_)
        _.run()
        depend_nonexists_ins.add_depend_class(_)

        # EMAの日付をすべて今日にして、時間で切れるか確かめる. 18:00のデータが存在する.
        # nonexistのインスタンスはあえて上書きせず, データがないようにする.
        depend_ins.ema["end"] = depend_ins.ema["end"].map(lambda x: set_hour_minute(datetime.today(), x))
        depended_ins.ema["end"] = depended_ins.ema["end"].map(lambda x: set_hour_minute(datetime.today(), x))

        depended_ins.run()
        depend_ins._depend_condition()
        depend_nonexists_ins._depend_condition()

        self.assertEqual(depend_ins.ema_from_.strftime("%H:%M"), "12:59")
        self.assertTrue(depend_nonexists_ins.ema.empty)

        # 時間が経っているかのテスト
        depend_ins.param["ema_time"]["interval"]["value"] = "00:00"
        # テストした時間が12:59よりあとであれば成功するはず
        # self.assertTrue(depend_ins._depend_condition())
        # self.assertTrue(depend_ins.run())
        depend_ins.param["ema_time"]["interval"]["value"] = "23:59"
        # self.assertFalse(depend_ins._depend_condition())
        # self.assertFalse(depend_ins.run())

    def test__run(self):
        """
        exists: [true or false]
        depend_classのときのテスト
        TODO 既に介入していれば介入しないことのテスト
        """
        param_exists = self.params[0].copy()
        param_exists["exists"] = True
        param_not_exists = self.params[0].copy()
        param_not_exists["exists"] = False

        exists_true_ins = EventTemplate(param_exists, self.user_info, self.ema, logger_file.logger(const.LOG_DIR))
        exists_true_ins = init_event_template(exists_true_ins)
        exists_false_ins = EventTemplate(param_not_exists, self.user_info, self.ema, logger_file.logger(const.LOG_DIR))
        exists_false_ins = init_event_template(exists_false_ins)
        self.ema["end"] = self.ema["end"].map(lambda x: set_hour_minute(datetime.today(), x))

        now = datetime.now()
        # 16:00~19:00以外にテストを実行するときのテストコード
        if now.hour < 16 or (now.hour == 19 and now.minute > 0) or now.hour > 19:
            self.assertTrue(exists_true_ins.run())
            self.assertFalse(exists_false_ins.run())

    def test_copy(self):
        self.assertIsInstance(self.et.copy(), EventTemplate)
        self.assertFalse(self.et is self.et.copy())


def init_event_template(ins):
    ins._init_ema_content()
    ins._init_ema_time()

    return ins


if __name__ == '__main__':
    """
        test command: python -m unittest test_this_file.py
    """
    unittest.main()
