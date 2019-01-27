from datetime import datetime
from pathlib import Path

import pandas as pd
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.EmaRecorder import EmaRecorder
from jitai.src.User import User

if __name__ == "__main__":

    logger = logger_file.logger(const.LOG_DIR)

    for index, user_info in const.USER_LIST.iterrows():

        user_data_dir = const.DATA_DIR / user_info["terminal_id"]

        # 前回EMAを取得した時間を取得する.
        if Path(user_data_dir / "ema_history.txt").exists():
            with open(user_data_dir / "ema_history.txt", "r") as f:
                last_ema_time = f.readlines()[-1]
        else:
            last_ema_time = ""

        # 今回のEMAを記録する.
        with open(user_data_dir / "ema_history.txt", "a") as f:
            f.write("\n" + datetime.today().strftime("%Y%m%d%H%M%S"))

        ema_recorder = EmaRecorder(logger, User(user_info["terminal_id"]))
        ema, _, _ = ema_recorder(from_date=last_ema_time, to_date="")

        if not ema.empty:

            if Path(user_data_dir / "ema.csv").exists():
                prev_ema = pd.read_csv(user_data_dir / "ema.csv")
                ema = pd.concat([prev_ema, ema], axis=0)

            ema.to_csv(user_data_dir / "ema.csv")

            logger.info("EMA of {} updated .".format(user_info["terminal_id"]))
