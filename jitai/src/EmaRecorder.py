from pathlib import Path

import pandas as pd
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.utils import access_api


class EmaRecorder:
    """
    回答完了、中断、時間切れそれぞれでデータがないものは、空のdataframeが返る.
    """
    def __init__(self, logger, user):
        self.logger = logger
        self.user = user
        self.data_dir = Path(const.DATA_DIR) / self.user.terminal_id
        self.from_date = ""
        self.to_date = ""
        self.save_df = False

    def __call__(self, from_date="", to_date="", save_df=False, *args, **kwargs):
        self.from_date = from_date
        self.to_date = to_date
        self.save_df = save_df
        return self._arrange_df()

    def _list_to_df(self, df_list, csv_name):
        if len(df_list):
            df = pd.concat(df_list, axis=0)
            # timeout以外のとき
            if csv_name in ["answer", "interrupt"]:
                df["start"] = pd.to_datetime(df['start'])
                df["end"] = pd.to_datetime(df['end'])
                df = df.astype({"question_number": int, "question": str})
                df = df.reset_index().rename(columns={"index": "q_index"})
                df = df.applymap(lambda x: str(x).replace("\n", "").replace("\r", ""))
            if self.save_df:
                df.to_csv(self.data_dir / f"{csv_name}.csv")
        else:
            df = pd.DataFrame()

        return df

    def _arrange_df(self):
        self.logger.info("ema recording started")

        # fromとtoが空欄だと全件取ってくる
        duration = "from=" + self.from_date + "&to=" + self.to_date
        url = Path(const.BASE_URL) / const.API_URL / const.MODE_URL["ema"] / self.user.terminal_id / str("csv?"+duration)
        content = access_api(self.logger, "http://" + str(url))

        # データが一つもない場合
        if len(content) < 10:
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
                df = pd.DataFrame(columns=df_columns)
                event = one_line.split(",")[3]
                answer_list.append(df)
                answer_flag = True
                interrupt_flag = False
                continue
            elif "中断" in one_line:
                df = pd.DataFrame(columns=df_columns)
                event = one_line.split(",")[3]
                interrupt_list.append(df)
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
                df = df.T
                df["event"] = event
                interrupt_list[-1] = pd.concat([interrupt_list[-1], df], axis=0, sort=True)
            # 回答完了のデータである場合
            elif answer_flag:
                df = pd.DataFrame(one_line.split(","), index=df_columns, columns=[len(answer_list)-1])
                df = df.T
                df["event"] = event
                answer_list[-1] = pd.concat([answer_list[-1], df], axis=0, sort=True)
            else:
                continue

        answer_df = self._list_to_df(answer_list, "answer")
        interrupt_df = self._list_to_df(interrupt_list, "interrupt")
        timeout_df = self._list_to_df(timeout_list, "timeout")

        return answer_df, interrupt_df, timeout_df


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)

