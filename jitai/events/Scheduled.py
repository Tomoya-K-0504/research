from jitai.events.EventTemplate import EventTemplate


class Scheduled(EventTemplate):
    def __init__(self, param, ema, user_info, logger):
        super(Scheduled, self).__init__(
            param=param, user_info=user_info, ema=ema, logger=logger)
        self._init_ema_content()
        self._init_ema_time()
        self.ema = ema[ema["event"] == "質問に回答する"]

    def run(self):
        return super(Scheduled, self).run()
