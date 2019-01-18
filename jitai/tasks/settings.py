import yaml
from datetime import datetime, timedelta
from pathlib import Path

from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Intervene import Intervene
from jitai.src.Jitai import Jitai as BaseJitai
from jitai.tasks.wake import Wake
from jitai.tasks.sleep import Sleep
from jitai.src.Logic import Logic
from jitai.src.utils import get_token, set_hour_minute


CLASS_CONVERTER = {"mother_wake": Wake, "mother_sleep": Sleep}

"""

event: ["sleep", "wake", "nap", "scheduled", "default"]
ema_time: ["set_time", "interval"]
ema_time_values: [["from", "to"], ""]
intervene_time: {"set_time", "interval"}

"""

# No.3の介入
params = yaml.load("""
- event: mother_sleep
  ema_time: 
    set_time:
        from: "19:00"
- event: mother_wake
  ema_time: 
    set_time:
        from: "2:00"
        to: "5:00"
"""
)


class Pipeline:
    def __init__(self, steps):
        self.steps = steps

    def jitai(self):
        pass


if __name__ == "__main__":
    pipeline = Pipeline()
    for param in params:
        Jitai = CLASS_CONVERTER[param["event"]]
        jitai = Jitai()