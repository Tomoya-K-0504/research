from jitai.events.EventTemplate import EventTemplate


class Weather(EventTemplate):
    def __init__(self, param, ema, user_info, logger):
        super(Weather, self).__init__(
            param=param, user_info=user_info, ema=ema, logger=logger
        )
        # TODO
        self.ema = ema[ema["event"] == "起床"]

    def run(self):
        return super(Weather, self).run()
