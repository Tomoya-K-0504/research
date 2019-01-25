from jitai.events.EventTemplate import EventTemplate


class MotherWake(EventTemplate):
    def __init__(self, param, ema, user_info, logger):
        super(MotherWake, self).__init__(
            param=param, user_info=user_info, ema=ema, logger=logger
        )
        self._init_ema_content()
        self._init_ema_time()
        self.ema = ema[ema["event"] == "母の起床"]

    def run(self):
        return super(MotherWake, self).run()
