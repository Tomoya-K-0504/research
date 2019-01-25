import unittest
from datetime import datetime
from pathlib import Path
from unittest import TestCase

import pandas as pd
import yaml
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.events.Scheduled import Scheduled
from jitai.src.utils import set_hour_minute


class TestScheduled(TestCase):

    def setUp(self):

        wake_test_case_dir = Path("testcases") / "mother_wake"
        self.ema = pd.read_csv(wake_test_case_dir / "model_test_case.csv", index_col=0)
        self.ema["end"] = pd.to_datetime(self.ema["end"])
        # EMAの日付をすべて今日にして、時間で切れるか確かめる.
        self.ema["end"] = self.ema["end"].map(lambda x: set_hour_minute(datetime.today(), x))
        self.user_info = const.USER_LIST.iloc[0]

        with open(const.PJ_ROOT / "yamls" / "scheduled_test.yml") as f:
            params = yaml.load(f)
        self.sc_true = Scheduled(params[0].copy(), self.ema.copy(), self.user_info, logger_file.logger(const.LOG_DIR))
        false_param = params[0].copy()
        false_param["ema_time"]["set_time"]["from"] = "13:00"
        false_param["ema_time"]["set_time"]["to"] = "17:00"
        self.sc_false = Scheduled(false_param, self.ema.copy(), self.user_info, logger_file.logger(const.LOG_DIR))

    def test_run(self):
        self.assertTrue(self.sc_true.run())
        self.assertFalse(self.sc_false.run())


if __name__ == '__main__':
    # test command: python -m unittest test_this_file.py
    unittest.main()
