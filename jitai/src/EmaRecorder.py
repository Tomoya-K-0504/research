import re
import sys
import time
import json
from datetime import timedelta, datetime
from pathlib import Path

from jitai.config import const
import pandas as pd
import requests
from bs4 import BeautifulSoup



from jitai.config import logger as logger_file
from jitai.src.utils import access_api, get_token
from jitai.src.Logic import Logic


class EmaRecorder:
    """
    回答完了、中断、時間切れそれぞれでデータがないものは、空のdataframeが返る.
    """
    def __init__(self, logger, data_path):
        self.logger = logger
        self.data_path = data_path

    def __call__(self, *args, **kwargs):
        return self._arrange_df()

    def _list_to_df(self, df_list, csv_name, save=True):
        if len(df_list):
            df = pd.concat(df_list, axis=0)
            # timeout以外のとき
            if csv_name in ["answer", "interrupt"]:
                df = df.astype({"start": datetime, "end": datetime, "question_number": int, "answer": int})
            if save:
                df.to_csv(self.data_path / f"{csv_name}_df.csv")
        else:
            df = pd.DataFrame()

        return df

    def _arrange_df(self):
        self.logger.info("ema recording started")

        # TODO 期間の指定
        url = Path(const.BASE_URL) / const.API_URL / const.MODE_URL["ema"] / const.MACHINE_ID / "csv"
        content = access_api(self.logger, "http://" + str(url))

        # データが一つもない場合
        if len(content) == 0:
            return (pd.DataFrame(), ) * 3

        content_lines = content.split("\n")[:-1]

        df_columns = ["start", "end", "question_number", "question", "answer"]
        time_out_columns = ["start", "end", "kind", "question", "protocol"]

        # 回答完了の行から次の回答完了の行までを抽出する
        answer_list = []
        interrupt_list = []
        timeout_list = []
        for one_line in content_lines:
            if "回答完了" in one_line:
                answer_list.append(pd.DataFrame(columns=df_columns))
                answer_flag = True
                interrupt_flag = False
                continue
            elif "中断" in one_line:
                interrupt_list.append(pd.DataFrame(columns=df_columns))
                answer_flag = False
                interrupt_flag = True
                continue
            elif "時間切れ" in one_line:
                df = pd.DataFrame(one_line.split(",")[:-1], index=time_out_columns, columns=[len(timeout_list)])
                timeout_list.append(df.T)
                answer_flag = False
                interrupt_flag = False
                continue

            # 中断したデータである場合
            if interrupt_flag:
                df = pd.DataFrame(one_line.split(","), index=df_columns, columns=[len(interrupt_list)-1])
                interrupt_list[-1] = pd.concat([interrupt_list[-1], df.T], axis=0)
            # 回答完了のデータである場合
            elif answer_flag:
                df = pd.DataFrame(one_line.split(","), index=df_columns, columns=[len(answer_list)-1])
                answer_list[-1] = pd.concat([answer_list[-1], df.T], axis=0)
            else:
                continue

        answer_df = self._list_to_df(answer_list, "answer")
        interrupt_df = self._list_to_df(interrupt_list, "interrupt")
        timeout_df = self._list_to_df(timeout_list, "timeout")

        return answer_df, interrupt_df, timeout_df


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)

