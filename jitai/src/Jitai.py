from abc import ABC
from abc import abstractmethod

import re
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

from config import const
from jitai.src.User import User
import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import logger as logger_file
from jitai.src.utils import access_api, get_token
from jitai.src.Intervene import Intervene
from jitai.src.EmaRecorder import EmaRecorder
from jitai.src.Logic import Logic


class Jitai(ABC):
    def __init__(self, user_info, logger, prev_ema_file):
        self.user = User(user_info["terminal_id"])
        self.logger = logger
        self.data_dir = Path(const.DATA_DIR) / self.user.terminal_id
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.ema_recorder = EmaRecorder(self.logger, self.user)
        self.prev_ema_file = prev_ema_file
        self.prev_ema_date = ""
        self.answer_df = pd.DataFrame()
        self.ema_date_to_use = ""

    # 介入を行うときの処理を記述
    def __call__(self, logic, timing="now", set_time="", delay_day=0, delay_hour=0, delay_minute=0, *args, **kwargs) -> None:
        logic = logic if logic else Logic(self.logger)
        intervene = Intervene(self.logger, self.user)

        answer_df, interrupt_df, timeout_df = self.ema_recorder(from_date="", to_date="")

        message_label = logic(answer_df, interrupt_df)

        if message_label:
            # トークンの取得
            token = get_token(self.logger)

            if timing == "now":
                intervene_time = datetime.today()
            elif timing == "interval":
                intervene_time = datetime.today() + timedelta(days=delay_day, hours=delay_hour, minutes=delay_minute)
            elif timing == "set_time":
                time = datetime.strptime(set_time, "%H%M")
                t = datetime.today() + timedelta(days=delay_day)
                intervene_time = datetime(t.year, t.month, t.day, time.hour, time.minute)
            intervene(message_label, token, intervene_time)

    # EMAをとってくる
    def _fetch_ema(self, from_date="", to_date="") -> None:
        self.answer_df, _, _ = self.ema_recorder(from_date=from_date, to_date=to_date)

    # 前のEMAの読み込み方を記述.
    @abstractmethod
    def _load_prev_ema(self) -> object:
        return None

    # 外部からEMAのチェックを行うメソッド. fetchとcheckと分けたのは、checkのテストをしやすくするため
    @abstractmethod
    def check_ema(self):
        self._fetch_ema()
        return self._check_ema()

    # EMAに更新があったかを判定するロジックを記述.
    @abstractmethod
    def _check_ema(self) -> bool:
        return False
