import json
import sys

import requests

from config import const


def access_api(logger, url, method="get", headers="", data=""):
    # スクレイピング先のサーバーに負荷がかかりすぎないよう、0.5秒おく
    # time.sleep(0.5)

    logger.info(f"accessing {url}")
    if method == "get":
        response = requests.get(url).content.decode("shift-jis")
    elif method == "post":
        response = requests.post(url, headers=headers, data=json.dumps(data))
    else:
        logger.error("bad method sent to access_api function: {method}")
        sys.exit(1)

    logger.info("got response.")

    return response


def get_token(logger):

    body = {"loginid": const.LOGIN_ID, "loginpassword": const.PASSWORD}
    response = access_api(logger, f"https://{const.BASE_URL}/{const.API_URL}/login", "post", const.HEADERS, body)
    token = json.loads(response.content.decode("utf-8"))["token"]

    logger.info("got token.")

    return token
