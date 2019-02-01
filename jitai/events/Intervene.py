from datetime import datetime, timedelta
from pathlib import Path

from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.utils import access_api, set_hour_minute, get_token


class Intervene:
    def __init__(self, param, ema, user_info, logger):
        self.param = param
        self.user_info = user_info
        self.message = param["message"]
        self.logger = logger

        # 時間に関する設定
        if list(param["intervene_time"].keys())[0] == "set_time":
            if param["intervene_time"]["set_time"] == "now":
                self.intervene_time = "now"
            else:
                set_time = datetime.strptime(param["intervene_time"]["set_time"], "%H:%M")
                self.intervene_time = set_hour_minute(datetime.today(), set_time).strftime("%Y%m%d%H%M")

        if list(param["intervene_time"].keys())[0] == "interval":
            t = datetime.strptime(param["intervene_time"]["interval"], "%H:%M")
            self.intervene_time = (datetime.today() + timedelta(hours=t.hour, minutes=t.minute)).strftime("%Y%m%d%H%M")

    def _body_json(self, title, body, delivery="now", popup=1, vibration=0):
        return {
            "msg": {
                "title": title,
                "body": body,
                "delivery": delivery,
                "popup": str(popup),
                "vibration": str(vibration)
            }
        }

    def _depend_condition(self):
        # depend_classの最後のEMAからinterval時間経過していればTrue, そうでなければFalseを返す.
        # TODO 要テスト
        if self.depend_class.run():
            last_ema_time = self.depend_class.ema.loc[self.depend_class.ema.shape[0] - 1, "end"]
            t = datetime.strptime(self.param["intervene_time"]["interval"], "%H:%M")
            if last_ema_time + timedelta(hours=t.hour, minutes=t.minute) <= datetime.today():
                self.logger.info("depend class true and passed time enough to intervene")
                return True
            self.logger.info("depend class true but passed time not enough to intervene")
            return False
        else:
            self.logger.info("depend class false, so stopped intervene.")
            return False

    def __call__(self, *args, **kwargs):

        if hasattr(self, "depend_class"):
            if not self._depend_condition():
                return False

        res = self.intervene()

        self.logger.info(res)

    def intervene(self):

        token = get_token(self.logger)

        # headerを作成する
        header = const.HEADERS
        header["Authorization"] = "Bearer: " + token

        payload = self._body_json(
            title="",
            body=self.message,
            delivery=self.intervene_time,
        )
        url = Path(const.BASE_URL) / const.API_URL / const.MODE_URL["interrupt"] / self.user_info["terminal_id"]
        res = access_api(self.logger, "https://" + str(url), method="post", headers=const.HEADERS, data=payload)

        return res

    def add_depend_class(self, depend_class):
        self.depend_class = depend_class


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)
