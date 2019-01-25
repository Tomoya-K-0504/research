from unittest import TestCase
from jitai.src.Jitai import Jitai

from datetime import datetime, timedelta
from pathlib import Path

from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Intervene import Intervene
from jitai.src.Jitai import Jitai
from jitai.src.Logic import Logic
from jitai.src.utils import get_token


class TestJitai(TestCase):

    def setUp(self):
        logger = logger_file.logger(const.LOG_DIR)
        prev_ema_date_file = "prev_ema_date.txt"

        for index, user_info in const.USER_LIST.iterrows():
            jitai = Jitai(user_info, logger, prev_ema_date_file)
            # emaの更新があり、かつ設定睡眠時間を過ぎているか確認する. 条件を満たしたときはjitai.prev_ema_dateの更新も行う.
            if jitai.check_ema():
                logger.info("machine id: {} will be intervened.".format(jitai.user.terminal_id))
                jitai()
                # 最新EMA時間の保存
                if Path(const.DATA_DIR / jitai.user.terminal_id / "answer.csv").exists():
                    with open(Path(const.DATA_DIR / jitai.user.terminal_id / prev_ema_date_file), "w") as f:
                        f.write(jitai.prev_ema_date.strftime('%Y%m%d%H%M%S') + ",True\n")
        jitai = Jitai()

    def test__load_prev_ema(self):
        a = ""

    def test_check_ema(self):
        self.fail()

    def tearDown(self):
        print("tearDown")
        del self.x


if __name__ == '__main__':
    """
        test command: python -m unittest test_this_file.py
    """
    unittest.main()
