from unittest import TestCase
from jitai.src.Jitai import Jitai
import unittest

from datetime import datetime, timedelta
from pathlib import Path

from datetime import datetime, timedelta
from pathlib import Path

import jpholiday
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Dams import Dams
from jitai.src.Intervene import Intervene
from jitai.tasks.wake import Wake, WakeLogic
from jitai.src.LivedoorApi import get_weather_info
from jitai.src.Logic import Logic
from jitai.src.utils import get_token


class TestWake(TestCase):

    def setUp(self):
        """
        - 設定時間を夜11時, 夜1時の両方
        1. not_ema...まだEMAをしていない端末
        2. ema__before_6_hours...EMAをしていて、最後のEMAが6時間以前の端末
        3. ema__within_6_hours__no_problem...EMAをしていて、最後のEMAが6時間以内で、問題ない端末
        4. ema__within_6_hours__problems...EMAをしていて、最後のEMAが6時間以内で、問題ある端末
        """

        self.logger = logger_file.logger(const.LOG_DIR)
        self.prev_ema_file = "prev_ema_wake.txt"
        self.not_ema = Wake(const.USER_LIST.iloc[0, :], self.logger, self.prev_ema_file)
        self.ema__before_6_hours = Wake(const.USER_LIST.iloc[1, :], self.logger, self.prev_ema_file)
        self.ema__within_6_hours__no_problem = Wake(const.USER_LIST.iloc[2, :], self.logger, self.prev_ema_file)
        self.ema__within_6_hours__problems = Wake(const.USER_LIST.iloc[2, :], self.logger, self.prev_ema_file)
        a, b, c = self.not_ema.ema_recorder(from_date="", to_date="")
        _ = 1

    def test___call__(self):
        # 介入が行われる可能性があるのはこれだけ...check_ema = True のもの
        logic = WakeLogic(self.logger)

        super.__call__(logic=logic)
        logic = WakeLogic(self.logger)

        # 介入がないことを手元で確認する
        self.ema__within_6_hours__no_problem(logic=logic)
        # 介入があることを手元で確認する
        self.ema__within_6_hours__problems(logic=logic)

    def test_check_ema(self):
        """

        """
        self.assertFalse(self.not_ema.check_ema())
        self.assertFalse(self.ema__before_6_hours.check_ema())
        self.assertTrue(self.ema__within_6_hours__no_problem.check_ema())
        self.assertTrue(self.ema__within_6_hours__problems.check_ema())

    def test__load_prev_ema(self):
        # -> (datetime, bool)
        _, flag = self.not_ema._load_prev_ema()
        self.assertFalse(flag)
        _, flag = self.ema__before_6_hours._load_prev_ema()
        self.assertFalse(flag)
        _, flag = self.ema__within_6_hours__no_problem._load_prev_ema()
        self.assertTrue(flag)
        _, flag = self.ema__within_6_hours__problems._load_prev_ema()
        self.assertTrue(flag)
