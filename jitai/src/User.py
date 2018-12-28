

class User:
    def __init__(self, terminal_id, ema=""):
        self.terminal_id = terminal_id
        self.ema = ema
        self.anxious = 0
        self.positive = 0
        self.negative = 0
        self.depressive = self.negative - self.positive
        self.pain = 0
        self.sleepy = 0
        self.stressed = 0
        self.tired = 0
        self._ema_update()

    def _ema_update(self):
        pass
