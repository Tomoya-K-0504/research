import sched, time, datetime, threading
import re
import sys
import time
import json
from datetime import timedelta
from pathlib import Path

from config import const
import pandas as pd
from jitai.src.EmaRecorder import EmaRecorder
from jitai.src.Jitai import Jitai
import requests
from bs4 import BeautifulSoup

from config import logger as logger_file
from jitai.src.utils import access_api, get_token
# 参考サイト→http://www.bokupy.com/detail/63#time_schedule-wait


def processing(a='3', b='goal'):
    print(datetime.datetime.now(), a, b)


def schedule():
    s = sched.scheduler(time.time, time.sleep)

    et1 = datetime.datetime(2018, 5, 7, 19)  # 実行する時間の作成
    et1 = int(time.mktime(et1.timetuple()))  # UNIX時間に変換

    while True:
        print(datetime.datetime.now(), 'start')
        s.enterabs(et1, 1, processing, argument=('event1',))
        s.enterabs(5, 2, processing, kwargs={'a': 'event2', 'b': 'Yes!'})

        s.run()
        if stop is not None:
            print(datetime.datetime.now(), 'stop of time_schedule')
            break


def control(logger):

    # 例
    # t1 = threading.Thread(name='rename worker1', target=worker1)
    # t2 = threading.Thread(target=worker2, args=(100,), kwargs={'y': 200})
    # t1.setDaemon(True)
    # t1 スレッドの完了を待つ
    # t1.join()
    # thread_obj = threading.Thread(target=monitor_ema, args=(logger, ))
    # thread_obj.start()

    jitai = Jitai(const.MACHINE_ID, logger)
    time_to_sleep = 3
    while not jitai.check_ema_updates():
        time.sleep(time_to_sleep)
    jitai()


if __name__ == '__main__':
    logger = logger_file.logger(const.LOG_DIR)
    control(logger)
