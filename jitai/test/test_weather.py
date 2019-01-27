import copy
from datetime import datetime, timedelta
from unittest import TestCase

import yaml
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.events.Baby import Baby
from jitai.src.utils import set_hour_minute, test_setup


class TestWeather(TestCase):

    def setUp(self):
        self = test_setup(self)
        logger = logger_file.logger(const.LOG_DIR)

        # EMAの日付をすべて今日と昨日にする
        self.ema["end"] = self.ema["end"].map(lambda x: set_hour_minute(datetime.today(), x))
        self.ema.loc[:5, "end"] = self.ema.loc[:5, "end"] - timedelta(days=1)

        with open(const.PJ_ROOT / "yamls" / "no_14_late.yml") as f:
            params = yaml.load(f)
        self._true = Baby(params[0].copy(), self.ema.copy(), self.user_info, logger=logger)
        false_param = copy.deepcopy(params[0])
        false_param["ema_time"]["set_time"]["from"] = "12:00"
        false_param["ema_time"]["set_time"]["to"] = "17:00"
        self.bw_false = Baby(false_param, self.ema.copy(), self.user_info, logger=logger)

    def test_run(self):
        # 今回はexistsがfalseなので、EMAが存在するbw_trueのほうがfalseが返る
        self.assertFalse(self.bw_true.run())
        self.assertTrue(self.bw_false.run())

