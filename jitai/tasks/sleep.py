from datetime import datetime, timedelta
from pathlib import Path

from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Intervene import Intervene
from jitai.src.Jitai import Jitai
from jitai.src.Logic import Logic
from jitai.src.utils import get_token


class Sleep(Jitai):
    def __init__(self, user_info, logger, prev_ema_file):
        super(Sleep, self).__init__(user_info, logger, prev_ema_file)
        self.time_to_sleep = datetime.strptime(user_info["time_to_sleep"], "%H:%M")

    def __call__(self, *args, **kwargs) -> None:
        logic = SleepLogic(self.logger)

        super.__call__(logic=logic)

    def check_ema(self) -> bool:
        # 前回の更新分をとってくる
        # if Path(const.DATA_DIR / self.user.terminal_id / "answer.csv").exists():
        #     df = pd.read_csv(const.DATA_DIR / self.user.terminal_id / "answer.csv", index_col=0)
        # else:
        #     df = pd.DataFrame()
        today = datetime.today()

        # 設定時刻を過ぎていない場合は必ず介入しない
        sleep_time = datetime(today.year, today.month, today.day, self.time_to_sleep.hour, self.time_to_sleep.minute)
        if datetime.now() < sleep_time:
            self.logger.info("Now is before {}, so will not send notification".format(sleep_time))
            return False

        # prev_ema_dateの更新
        self.prev_ema_date, sent_flag = self._load_prev_ema()

        # prev_ema_dateが昨日以前ならば、日をまたいでいるので必ず介入していない
        if self.prev_ema_date < today:
            sent_flag = False

        # 昨日今日の更新分をとってくる
        answer_df, interrupt_df, timeout_df = self.ema_recorder(from_date=(today-timedelta(days=1)).date().strftime('%Y%m%d'))

        # EMAが昨日今日で１件もない
        if not len(answer_df):
            self.logger.info("No EMA data exists in yesterday and today")
            return False

        # 6時間前までのデータにする
        answer_df = answer_df[answer_df["end"] > datetime.now() - timedelta(hours=6)]

        # answer_dfが0件か、まだ介入しておらず、sleepのEMAが存在していない場合は, 介入を行うのでTrue
        if not len(answer_df) or ((not sent_flag) and "sleep" in list(set(answer_df["event"]))):
            self.logger.info("Now is after {} and EMA when sleep hasn't completed, will send notification".format(sleep_time))
            return True

        self.logger.info("sleep EMA has done or already sent notification")
        return False

    def _load_prev_ema(self) -> (datetime, bool):
        path = Path(const.DATA_DIR / self.user.terminal_id / self.prev_ema_file)
        if path.exists():
            with open(path, "r") as f:
                latest_record = f.read().split("\n")[-2]
                sent_flag = True if latest_record.split(",")[1] == "True" else False
                return datetime.strptime(latest_record.split(",")[0], '%Y%m%d%H%M%S'), sent_flag
        else:
            # まだEMAをとっていないときは昨日の日付とFalseを返す. 睡眠は一日単位のため、前日より以前しか記録がない時点でだめなので.
            return datetime.today() - timedelta(days=1), False


class SleepLogic(Logic):
    def __init__(self, logger):
        super(SleepLogic, self).__init__(logger)

    def __call__(self, answer_df, interrupt_df, *args, **kwargs):
        # "ストレスがある" が75を超えたら、眠る準備をしましょうメッセージ
        times_answered = list(set(answer_df.index))
        if int(answer_df[answer_df["question"] == "ストレスがある"].loc[times_answered[-1], "answer"]) > 75:
            return "time_to_sleep"
        else:
            return "none"


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)
    logger.info("sleep JITAI started.")
    prev_ema_date_file = "prev_ema_sleep.txt"

    for index, user_info in const.USER_LIST.iterrows():
        jitai = Sleep(user_info, logger, prev_ema_date_file)
        # emaの更新があり、かつ設定睡眠時間を過ぎているか確認する. 条件を満たしたときはjitai.prev_ema_dateの更新も行う.
        if jitai.check_ema():
            logger.info("machine id: {} will be intervened.".format(jitai.user.terminal_id))
            jitai()
            # 最新EMA時間の保存
            if Path(const.DATA_DIR / jitai.user.terminal_id / "answer.csv").exists():
                with open(Path(const.DATA_DIR / jitai.user.terminal_id / prev_ema_date_file), "w") as f:
                    f.write(jitai.prev_ema_date.strftime('%Y%m%d%H%M%S') + ",True\n")

