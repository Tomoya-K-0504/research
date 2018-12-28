from pathlib import Path

from jitai.config import const
from jitai.src.utils import access_api
from jitai.config import logger as logger_file


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

    def __call__(self, message_label, token, *args, **kwargs):
        # headerを作成する
        header = const.HEADERS
        header["Authorization"] = "Bearer: " + token

        payload = self._body_json(const.INTERRUPT_MSG[message_label]["title"], const.INTERRUPT_MSG[message_label]["body"])
        url = Path(const.BASE_URL) / const.API_URL / const.MODE_URL["interrupt"] / self.user.terminal_id
        res = access_api(self.logger, "https://" + str(url), method="post", headers=const.HEADERS, data=payload)

        self.logger.info(res)


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)
