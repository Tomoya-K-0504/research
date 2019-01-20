import yaml
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


CLASS_CONVERTER = {"mother_wake": Wake, "mother_sleep": Sleep}

"""

condition_name: sth
event: ["sleep", "wake", "nap", "scheduled", "default"]
ema_time: ["set_time", "interval"]
ema_time_values: [["from", "to"], ""]
intervene_time: {"set_time", "interval"}

"""

# No.3の介入
params = yaml.load("""
- condition_name: sleep_before_evening
  event: mother_sleep
  ema_time: 
    set_time:
        from: "19:00"
- condition_name: wake_early_morning
  event: mother_wake
  ema_time: 
    set_time:
        from: "2:00"
        to: "5:00"
"""
)


class Pipeline:
    """
    パイプラインが満たすべき条件は以下に示す
    - stepsによって処理を進める.
    - 最終ステップ(介入)以外の各stepで, EMAや実行時刻等に条件を適用し、条件を満たせばTrueで次ステップへ処理済みEMAを渡す
    - 各ステップで条件を満たさない場合は、次ステップにFalseを渡し、

    """
    def __init__(self, steps):
        self.steps = steps

    def jitai(self):
        pass


class Step(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


if __name__ == "__main__":
    steps = []
    for param in params:
        Jitai = CLASS_CONVERTER[param["event"]]
        jitai = Jitai(param)
        steps.append((params["condition_name"], jitai))
    pipeline = Pipeline(steps)
    pipeline()
