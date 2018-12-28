from abc import ABC
from abc import abstractmethod

import re
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

from jitai.config import const
from jitai.src.User import User
import pandas as pd
import requests
from bs4 import BeautifulSoup

from jitai.config import logger as logger_file
from jitai.src.utils import access_api, get_token
from jitai.src.Intervene import Intervene
from jitai.src.EmaRecorder import EmaRecorder
from jitai.src.Logic import Logic


class Jitai(ABC):
    def __init__(self, terminal_id, logger):
        self.user = User(terminal_id)
        self.logger = logger
        self.data_dir = Path(const.DATA_DIR) / self.user.terminal_id
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.ema_recorder = EmaRecorder(self.logger, self.user)

        self.prev_ema_date = self._load_prev_ema_date()   # 前のEMAがないときは空文字

    # @abstractmethod
    # def hoge(self):
    #     pass

    def __call__(self, *args, **kwargs):
        logic = Logic(self.logger)
        intervene = Intervene(self.logger, self.user)

        answer_df, interrupt_df, timeout_df = self.ema_recorder()

        message_label = logic(answer_df, interrupt_df)

        if message_label:
            # トークンの取得
            token = get_token(self.logger)

            intervene(message_label, token)

    def _load_prev_ema_date(self):
        path = Path(const.DATA_DIR / self.user.terminal_id / "prev_ema_date.txt")
        if path.exists():
            with open(path, "r") as f:
                return datetime.strptime(f.read().split("\n")[-2], '%Y%m%d%H%M%S')
        else:
            # 一回目は30日分をとってくる
            return datetime.today() - timedelta(days=30)

    def check_ema_updates(self):

        # 前回の更新分をとってくる
        # if Path(const.DATA_DIR / self.user.terminal_id / "answer.csv").exists():
        #     df = pd.read_csv(const.DATA_DIR / self.user.terminal_id / "answer.csv", index_col=0)
        # else:
        #     df = pd.DataFrame()

        # 今回の更新分をとってくる
        answer_df, interrupt_df, timeout_df = self.ema_recorder(self.prev_ema_date.date().strftime('%Y%m%d'), datetime.today().date().strftime('%Y%m%d'), save_df=True)

        # answer_dfがないときとは、初回でかつEMAの記録がないときで、prev_ema_timeとanswer_dfの終了時間が同じときとは、EMAの記録があるが更新がないとき
        if len(answer_df) == 0 or self.prev_ema_date == datetime.strptime(answer_df["end"].values[-1][:-4], '%Y/%m/%d %H:%M:%S'):
            return False

        # prev_ema_dateの更新
        self.prev_ema_date = datetime.strptime(answer_df["end"].values[-1][:-4], '%Y/%m/%d %H:%M:%S')

        # TODO 時間まで指定できるようになったらこれでよい
        # return bool(len(answer_df))

        return True


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)
    for id in const.MACHINE_IDS.values():
        jitai = Jitai(id, logger)
        if jitai.check_ema_updates():
            logger.info("machine id: {} will be intervened.".format(jitai.user.terminal_id))
            jitai()
        # 保存されたEMAがある場合、最新EMA時間の保存
        if Path(const.DATA_DIR / jitai.user.terminal_id / "answer.csv").exists():
            with open(Path(const.DATA_DIR / jitai.user.terminal_id / "prev_ema_date.txt"), "w") as f:
                f.write(jitai.prev_ema_date.strftime('%Y%m%d%H%M%S') + "\n")

