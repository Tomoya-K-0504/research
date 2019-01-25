from jitai.events.EventTemplate import EventTemplate


class MotherSleep(EventTemplate):
    def __init__(self, param, ema, user_info, logger):
        super(MotherSleep, self).__init__(
            param=param, user_info=user_info, ema=ema, logger=logger
        )
        self._init_ema_content()
        self._init_ema_time()
        self.ema = ema[ema["event"] == "母の就寝"]

    def run(self):
        return super(MotherSleep, self).run()

