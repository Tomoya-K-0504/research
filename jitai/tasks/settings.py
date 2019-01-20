import yaml
import sys
from datetime import datetime, timedelta
from pathlib import Path
from abc import ABC
from abc import abstractmethod

from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Intervene import Intervene
from jitai.src.Jitai import Jitai as BaseJitai
from jitai.events import MotherWake
from jitai.tasks.wake import Wake
from jitai.tasks.sleep import Sleep
from jitai.src.Logic import Logic
from jitai.src.utils import get_token, set_hour_minute


"""
# interval_valueは, 2.5時間後のときは 02:30 のように書くこと.

- condition_name: sth
  event: [sleep or wake or nap or scheduled or  default]
  ema_content: [none or はつらつとした or 楽しい or 嬉しい or 暗い or 嫌な or 沈んだ or 気がかりな or 不安な or 心配な]
  # noneのとき、つまりEMAが選ぶ時間にあるかないかを見るとき
  ema_time: [set_time or interval]
    ema_time_values: ["from" and "to"] or interval_value
    exists: [true or false]
  # noneでない、つまりEMAのある項目が閾値以上/未満を見るとき
  threshold: value
  more_or_less: [more or less]
  ema_time: [set_time or interval]
    ema_time_values: ["from" and "to"] or interval_value
    exists: [true or false]
- intervene_type: [push or pull]
  # pushのとき
  intervene_time: [set_time or interval]
    ema_time_values: ["from" and "to"] or now or interval_value
    exists: [true or false]
  # pullのとき
  check_event: [sleep or wake or nap or scheduled or  default]
  event_after_time: [set_time or interval]
    ema_time_values: ["from" and "to"] or now or interval_value
    exists: [true or false]
    
"""

# No.3の介入
params = yaml.load("""
- condition_name: wake_early_morning
  event: MotherWake
  ema_content: none
  ema_time: 
    set_time:
        from: "16:00"
        to: "20:00"
  exists: true
- condition_name: sleep_before_evening
  event: MotherSleep
  ema_content: none
  ema_time: 
    set_time:
        from: "16:00"
        to: "19:00"
  exists: false
- event: Intervene
  intervene_type: push
  intervene_time: 
    set_time:
        now
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
        res = []
        for step in self.steps:
            res.append(step[1].jitai())

        return sum(res) == len(res)


def import_jitais(class_name):
    if class_name == "MotherWake":
        from jitai.events.MotherWake import MotherWake
        return MotherWake
    elif class_name == "MotherSleep":
        from jitai.events.MotherSleep import MotherSleep
        return MotherSleep
    elif class_name == "Intervene":
        from jitai.events.Intervene import Intervene


if __name__ == "__main__":

    # TODO どのファイルが端末IDのfor文を回すようにするのか. でも各介入設定ファイルではないよな.
    # TODO srcのJitaiを使うのか使わないのか.

    steps = []

    for param in params[:-1]:
        Jitai = import_jitais(param["event"])
        jitai = Jitai(param)
        steps.append((param["condition_name"], jitai))
    pipeline = Pipeline(steps)
    answer = pipeline.jitai()
    a = ""
