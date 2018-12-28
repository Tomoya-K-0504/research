from pathlib import Path
from datetime import datetime, timedelta

from config import const
from jitai.src.utils import access_api
from config import logger as logger_file


class Intervene:
    def __init__(self, logger, user):
        self.logger = logger
        self.user = user

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

    def __call__(self, message_label, token, delay_day=0, delay_hour=0, *args, **kwargs):

        # その人の状態に合わせて声掛けを行う. 何時頃どんな生活とかわかってれば.
        # 加速度が取れれば、睡眠してるとか運動してるとかわかって、EMAを送ったり介入を控えたりできる.

        # headerを作成する
        header = const.HEADERS
        header["Authorization"] = "Bearer: " + token

        payload = self._body_json(
            const.INTER_MSG[message_label]["title"],
            const.INTER_MSG[message_label]["body"],
            (datetime.today()+timedelta(days=delay_day)+timedelta(hours=delay_hour)).strftime("%Y%m%d%H%M"),
        )
        url = Path(const.BASE_URL) / const.API_URL / const.MODE_URL["interrupt"] / self.user.terminal_id
        res = access_api(self.logger, "https://" + str(url), method="post", headers=const.HEADERS, data=payload)

        self.logger.info(res)


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)
