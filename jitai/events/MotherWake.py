import os, sys, re
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from abc import ABC
from abc import abstractmethod

from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Intervene import Intervene
from jitai.src.EmaRecorder import EmaRecorder
from jitai.src.User import User
from jitai.src.Jitai import Jitai as BaseJitai
from jitai.tasks.wake import Wake
from jitai.tasks.sleep import Sleep
from jitai.src.Logic import Logic
from jitai.src.utils import get_token, set_hour_minute
from jitai.events.EventTemplate import EventTemplate


class MotherWake(EventTemplate):
    def __init__(self, param):
        user_info = const.USER_LIST.iloc[0]
        self.ema_recorder = EmaRecorder(logger_file.logger(const.LOG_DIR), User(user_info["terminal_id"]))
        super(MotherWake, self).__init__(param)

    def jitai(self):
        ema, _, _ = self.ema_recorder(from_date="", to_date="")
        ema = ema[ema["event"] == "起床"]
        ema = super(MotherWake, self).jitai(ema)
        if self.exists:
            return True if not ema.empty else False
        else:
            return True if ema.empty else False
