from abc import ABC
from abc import abstractmethod

#
# class BaseLogic:
#     def __init__(self, ema_list):
#         self.ema_df = ema_df
#         self.ema_quitted_df = ema_quitted_df

class Logic(ABC):
    def __init__(self, logger):
        self.logger = logger

    @abstractmethod
    def __call__(self, answer_df, interrupt_df, *args, **kwargs) -> str:
        # TODO 介入のロジックを考える
        # TODO その人の平均値を閾値とする
        # TODO 1. DAMSの計算を入れる

        return ""



