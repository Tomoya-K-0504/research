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
from jitai.tasks.jitai_template import EveryMinute
from jitai.src.LivedoorApi import get_weather_info
from jitai.src.Logic import Logic
from jitai.src.utils import get_token


class TestEveryMinute(TestCase):

    def setUp(self):
        """
        1. まだEMAをしていない端末
        2. EMAをしていて、

        """

        self.logger = logger_file.logger(const.LOG_DIR)
        self.prev_ema_file = "prev_ema_date.txt"
        self.jitai = EveryMinute(const.USER_LIST[0], self.logger, self.prev_ema_file)

    def test___call__(self):
        """

            """
        self.jitai()

    def test__load_prev_ema(self):
        """

            """
        a = ""

    def test_check_ema(self):
        self.assertTrue(self.jitai.check_ema())
        self.assertFalse(self.jitai.check_ema())

    def tearDown(self):
        print("tearDown")
        del self.jitai


class TestEveryMinuteLogic(TestCase):

    def setUp(self):
        """
        1. まだEMAをしていない端末
        2. EMAをしていて、最後のEMAが問題ない端末
        3. EMAをしていて、最後のEMAが問題ある端末

        """

        self.logger = logger_file.logger(const.LOG_DIR)
        self.prev_ema_file = "prev_ema_date.txt"
        self.jitai = EveryMinute(const.USER_LIST[0], self.logger, self.prev_ema_file)

    def test___call__(self):
        self.fail()


if __name__ == '__main__':
    """
        test command: python -m unittest test_this_file.py
    """
    unittest.main()

