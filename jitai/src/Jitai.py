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
    def __init__(self, terminal_id, logger, prev_ema_file):
        self.user = User(terminal_id)
        self.logger = logger
        self.data_dir = Path(const.DATA_DIR) / self.user.terminal_id
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.ema_recorder = EmaRecorder(self.logger, self.user)
        self.prev_ema_file = prev_ema_file
        self.prev_ema_date = ""

    # @abstractmethod
    # def hoge(self):
    #     pass

    # 介入を行うときの処理を記述
    @abstractmethod
    def __call__(self, *args, **kwargs) -> None:
        return None

    # 前のEMAの読み込み方を記述.
    @abstractmethod
    def _load_prev_ema(self) -> object:
        return None

    # EMAに更新があったかを判定するロジックを記述.
    @abstractmethod
    def check_ema(self) -> bool:
        return False
