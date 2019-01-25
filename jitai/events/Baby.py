from jitai.events.EventTemplate import EventTemplate

import pandas as pd


class Baby(EventTemplate):
    def __init__(self, param, ema, user_info, logger):
        super(Baby, self).__init__(
            param=param, user_info=user_info, ema=ema, logger=logger
        )

        # ema_contentに関しては特別に定義する.
        self.ema_content = param["ema_content"]

        self._init_ema_time()
        self.ema = ema[ema["event"] == "子どもに関する記録（日中）"]

    def _check_time(self):
        pass

    def _ema_content_not_none(self):
        # overrideすること.
        self.ema = self.ema[self.ema["answer"] == self.ema_content]

    def run(self):
        self._check_time()
        return super(Baby, self).run()
