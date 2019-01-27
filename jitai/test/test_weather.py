import copy
from datetime import datetime, timedelta
from unittest import TestCase

import yaml
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.events.Weather import Weather
from jitai.src.utils import set_hour_minute, test_setup


class TestWeather(TestCase):

    def setUp(self):
        self = test_setup(self)
        logger = logger_file.logger(const.LOG_DIR)

        # EMAの日付をすべて今日と昨日にする
        self.ema["end"] = self.ema["end"].map(lambda x: set_hour_minute(datetime.today(), x))
        self.ema.loc[:5, "end"] = self.ema.loc[:5, "end"] - timedelta(days=1)

        with open(const.PJ_ROOT / "yamls" / "weather_test.yml") as f:
            params = yaml.load(f)
        self.w_true = Weather(params[0].copy(), self.ema.copy(), self.user_info, logger=logger)
        false_param = copy.deepcopy(params[0])
        false_param["exists"] = False
        self.w_false = Weather(false_param, self.ema.copy(), self.user_info, logger=logger)

    def test_run(self):
        # 今回はexistsがfalseなので、EMAが存在するw_trueのほうがfalseが返る
        self.assertTrue(self.w_true.run())
        self.assertFalse(self.w_false.run())

