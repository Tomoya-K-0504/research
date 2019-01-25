import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from jitai.config import const


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


def set_hour_minute(day_date, hour_date):
    return datetime(day_date.year, day_date.month, day_date.day, hour_date.hour, hour_date.minute)


def import_events(class_name):
    if class_name == "MotherWake":
        from jitai.events.MotherWake import MotherWake
        return MotherWake
    elif class_name == "MotherSleep":
        from jitai.events.MotherSleep import MotherSleep
        return MotherSleep
    if class_name == "Baby":
        from jitai.events.Baby import Baby
        return Baby
    elif class_name == "EventTemplate":
        from jitai.events.EventTemplate import EventTemplate
        return EventTemplate
    elif class_name == "Scheduled":
        from jitai.events.Scheduled import Scheduled
        return Scheduled
    else:
        raise TypeError("event value should be in ['MotherWake', 'MotherSleep']")


def start_end_to_datetime(df):
    df["start"] = pd.to_datetime(df['start'])
    df["end"] = pd.to_datetime(df['end'])

    return df


def test_setup(ins):
    wake_test_case_dir = Path(const.PJ_ROOT / "test" / "testcases") / "mother_wake"
    ins.ema = pd.read_csv(wake_test_case_dir / "new_test_case.csv", index_col=0)
    ins.ema["end"] = pd.to_datetime(ins.ema["end"])
    ins.user_info = const.USER_LIST.iloc[0]

    return ins
