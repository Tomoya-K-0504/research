from unittest import TestCase
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
from jitai.events.Baby import Baby
from jitai.src.utils import set_hour_minute, test_setup


class TestBaby(TestCase):

    def setUp(self):
        self = test_setup(self)
        logger = logger_file.logger(const.LOG_DIR)

        # EMAの日付をすべて今日にして、時間で切れるか確かめる.
        self.ema["end"] = self.ema["end"].map(lambda x: set_hour_minute(datetime.today(), x))

        with open(const.PJ_ROOT / "yamls" / "baby_test.yml") as f:
            params = yaml.load(f)
        self.bw_true = Baby(params[0].copy(), self.ema.copy(), self.user_info, logger=logger)
        false_param = copy.deepcopy(params[0])
        false_param["ema_time"]["set_time"]["from"] = "12:00"
        false_param["ema_time"]["set_time"]["to"] = "17:00"
        self.bw_false = Baby(false_param, self.ema.copy(), self.user_info, logger=logger)

    def test_run(self):
        # 今回はexistsがfalseなので、EMAが存在するbw_trueのほうがfalseが返る
        self.assertFalse(self.bw_true.run())
        self.assertTrue(self.bw_false.run())
