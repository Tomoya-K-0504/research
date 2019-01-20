import os, sys, re
from datetime import datetime, timedelta
from pathlib import Path
from abc import ABC
from abc import abstractmethod

from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Intervene import Intervene
from jitai.src.Jitai import Jitai as BaseJitai
from jitai.tasks.wake import Wake
from jitai.tasks.sleep import Sleep
from jitai.src.Logic import Logic
from jitai.src.utils import get_token, set_hour_minute


class EventTemplate(ABC):
    def __init__(self, param):
        self.name = param["condition_name"]
        self.ema_content = param["ema_content"]
        if not self.ema_content == "none":
            self.threshold = param["threshold"]
            self.more_or_less = param["more_or_less"]
        self.ema_time = param["ema_time"]   # param["ema_time]"の値はdict
        if list(self.ema_time.keys())[0] == "set_time":
            from_ = datetime.strptime(self.ema_time["set_time"]["from"], "%H:%M")
            self.ema_from_ = set_hour_minute(datetime.today(), from_)
            to = datetime.strptime(self.ema_time["set_time"]["to"], "%H:%M")
            self.ema_to = set_hour_minute(datetime.today(), to)
        if list(self.ema_time.keys())[0] == "interval":
            t = datetime.strptime(self.ema_time["interval"]["value"], "%H:%M")
            self.ema_from_ = datetime.today() - timedelta(hours=t.hour, minutes=t.minute)
        self.exists = param["exists"]

    def _extract_about_time(self, ema):
        if list(self.ema_time.keys())[0] == "set_time":
            return ema[(ema["end"] >= self.ema_from_) & (ema["end"] <= self.ema_to)]
        else:
            return ema[ema["end"] >= self.ema_from_]

    def _ema_content_not_none(self, ema):
        if self.more_or_less == "more":
            return ema[ema[self.ema_content] > self.threshold]
        elif self.more_or_less == "less":
            return ema[ema[self.ema_content] < self.threshold]

    def jitai(self, ema):
        if not ema.empty:
            ema = self._extract_about_time(ema)

        if not ema.empty and not self.ema_content == "none":
            ema = self._ema_content_not_none(ema)

        return ema
