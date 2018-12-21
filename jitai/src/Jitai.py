from abc import ABC
from abc import abstractmethod

import re
import sys
import time
import json
from datetime import timedelta
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
        self.data_dir = Path(const.DATA_DIR) / str(self.user.user_id)
        self.ema_recorder = EmaRecorder(self.logger, self.data_dir)

        self.previous_data_len = 0

    # @abstractmethod
    # def hoge(self):
    #     pass

    def __call__(self, *args, **kwargs):
        self.data_dir.mkdir(exist_ok=True, parents=True)
        ema_recorder = EmaRecorder(self.logger, self.data_dir)
        logic = Logic(self.logger)
        intervene = Intervene(self.logger)

        answer_df, interrupt_df, timeout_df = ema_recorder()

        message_label = logic(answer_df, interrupt_df)

        # トークンの取得
        token = get_token(self.logger)

        intervene(message_label, token)

    def check_ema_updates(self):
        answer_df, interrupt_df, timeout_df = self.ema_recorder()

        # 一回目のとき
        if self.previous_data_len == 0:
            self.previous_data_len = len(answer_df)
            return False

        received = not self.previous_data_len == len(answer_df)

        self.previous_data_len = len(answer_df)

        return received


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)
    jitai = Jitai(const.MACHINE_ID, logger)
    jitai()
    _ = ""

