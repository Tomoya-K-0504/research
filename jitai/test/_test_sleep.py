from unittest import TestCase
from jitai.src.Jitai import Jitai
import unittest

import pandas as pd

from datetime import datetime, timedelta
from pathlib import Path

from datetime import datetime, timedelta
from pathlib import Path

import jpholiday
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Dams import Dams
from jitai.src.Intervene import Intervene
from jitai.tasks.sleep import Sleep, SleepLogic
from jitai.src.LivedoorApi import get_weather_info
from jitai.src.Logic import Logic
from jitai.src.utils import get_token


class TestSleep(TestCase):

    def setUp(self):
        """
        - 設定時間を夜11時, 夜1時の両方
        1. no_ema...まだEMAをしていない端末
        2. ema__before_6_hours...最後のEMAが6時間以前の端末
        3. send_flag_true_but_notify...今日以前に介入が行われている端末
        4. already_notified...今日既に介入が行われている端末
        4. last_not_sleep...最後のEMAが6時間以内で、最後のEMAが睡眠でない端末
        5. last_sleep...最後のEMAが6時間以内で、最後のEMAが睡眠である端末
        """

        self.logger = logger_file.logger(const.LOG_DIR)
        self.prev_ema_file = "prev_ema_sleep.txt"
        with open(const.DATA_DIR / const.USER_LIST.loc[2, "terminal_id"] / "test__prev_ema_sleep_true_before.txt", "w") as f:
            f.write("20190112124528,True\n")
        with open(const.DATA_DIR / const.USER_LIST.loc[2, "terminal_id"] / "test__prev_ema_sleep_true_after.txt", "w") as f:
            f.write("{},True\n".format(datetime.today().strftime("%Y%m%d%H%M%S")))

        sleep_test_case_dir = Path("testcases") / "sleep"
        df = pd.read_csv(sleep_test_case_dir / "model_test_case.csv", index_col=0)

        # EMAは1日前にして、設定睡眠時間をテスト実行時の時間の1時間後にすることで、過ぎないようにする
        df["end"] = datetime.today() - timedelta(days=1)
        const.USER_LIST.loc[2, "time_to_sleep"] = (datetime.today() + timedelta(hours=1)).strftime("%H:%M")

        self.no_ema = Sleep(const.USER_LIST.iloc[2, :], self.logger, self.prev_ema_file)
        self.no_ema.answer_df = pd.DataFrame(columns=df.columns)

        self.ema__before_6_hours = Sleep(const.USER_LIST.iloc[2, :], self.logger, self.prev_ema_file)
        self.ema__before_6_hours.answer_df = pd.read_csv("testcases/sleep/ema__before_6_hours.csv", index_col=0)

        # EMAが最新のものにして、設定睡眠時間をテスト実行時の時間にすることで、過ぎるようにする
        df["end"] = datetime.today()
        const.USER_LIST.loc[2, "time_to_sleep"] = (datetime.today()).strftime("%H:%M")

        self.send_flag_true_but_notify = Sleep(const.USER_LIST.iloc[2, :], self.logger, "test__prev_ema_sleep_true_before.txt")
        self.send_flag_true_but_notify.answer_df = df[df["event"] == "sleep"]
        self.already_notified = Sleep(const.USER_LIST.iloc[2, :], self.logger, "test__prev_ema_sleep_true_after.txt")
        self.already_notified.answer_df = df[df["event"] == "sleep"]

        self.last_not_sleep = Sleep(const.USER_LIST.iloc[2, :], self.logger, self.prev_ema_file)
        self.last_not_sleep.answer_df = df[df["event"] == "wake"]

        self.last_sleep = Sleep(const.USER_LIST.iloc[2, :], self.logger, self.prev_ema_file)
        self.last_sleep.answer_df = df[df["event"] == "sleep"]

    @unittest.skip("既に通過した")
    def test___call__(self):
        # 介入が行われる可能性があるのはこれだけ...check_ema = True のもの
        logic = SleepLogic(self.logger)

        # 介入がないことを手元で確認する
        self.last_not_sleep(logic=logic)
        # 介入があることを手元で確認する
        self.last_sleep(logic=logic)

    def test__check_ema(self):
        """

        """
        # self.assertFalse(self.no_ema.check_ema())
        # self.assertFalse(self.ema__before_6_hours.check_ema())
        self.assertTrue(self.send_flag_true_but_notify.check_ema())
        self.assertFalse(self.already_notified.check_ema())
        self.assertTrue(self.last_not_sleep.check_ema())
        self.assertTrue(self.last_sleep.check_ema())

    @unittest.skip("全体でのテスト実行時に確認する. 具体的には、test__check_emaで確認するため省略.")
    def test__load_prev_ema(self):
        pass

