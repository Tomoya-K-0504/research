from jitai.events.EventTemplate import EventTemplate
from jitai.src.LivedoorApi import get_weather_info


class Weather(EventTemplate):
    def __init__(self, param, ema, user_info, logger):
        self.param = param
        self.user_info = user_info
        self.logger = logger
        self.weather_content = param["weather"]
        self.exists = param["exists"]

    def _fetch_weather(self):
        return get_weather_info(self.user_info["zipcode"])

    def run(self):
        weather_forecast = self._fetch_weather()
        if self.exists:
            return self.weather_content in weather_forecast
        else:
            return self.weather_content not in weather_forecast
