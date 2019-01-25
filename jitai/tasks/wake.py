from datetime import datetime, timedelta
from pathlib import Path

import jpholiday
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Jitai import Jitai
from jitai.src.LivedoorApi import get_weather_info
from jitai.src.Logic import Logic


class Wake(Jitai):
    def __init__(self, user_info, logger, prev_ema_file):
        super(Wake, self).__init__(user_info, logger, prev_ema_file)
        self.postcode = user_info["postcode"]
        # self.time_to_wake = datetime.strptime(user_info["time_to_wake"], "%H:%M")

    def __call__(self, *args, **kwargs) -> None:
        logic = WakeLogic(self.logger, self.postcode)

        super(Wake, self).__call__(logic=logic)

    def check_ema(self) -> bool:

        today = datetime.today()

        # 午前5時から午前10時までは必ず介入しない
        # wake_time = datetime(today.year, today.month, today.day, self.time_to_wake.hour, self.time_to_wake.minute)
        if datetime.now() < datetime(today.year, today.month, today.day, 5, 0) or datetime.now() > datetime(today.year, today.month, today.day, 17, 0):
            self.logger.info("Now is before 5 am or after 10 am, so will not send notification")
            return False

        # prev_ema_dateの更新
        self.prev_ema_date, sent_flag = self._load_prev_ema()

        # prev_ema_dateが昨日以前ならば、日をまたいでいるので必ず介入していない
        if self.prev_ema_date < today - timedelta(days=1):
            sent_flag = False

        # 今日の更新分をとってくる
        answer_df, interrupt_df, timeout_df = self.ema_recorder(from_date=today.strftime('%Y%m%d'))

        # EMAが今日１件もない
        if not len(answer_df):
            self.logger.info("No EMA data exists today")
            return False

        # 実行している時間までのデータにする
        answer_df = answer_df[answer_df["end"] < datetime.now()]

        # wakeのEMAをしていて、介入を行っていない場合に介入を行う
        _ = list(set(answer_df["event"]))
        if len(answer_df) and (not sent_flag) and "wake" in list(set(answer_df["event"])):
            self.logger.info("Now is after 5 am and EMA about wake completed, will send notification")
            return True

        self.logger.info("wake EMA has't done or already sent notification")
        return False

    def _load_prev_ema(self) -> (datetime, bool):
        path = Path(const.DATA_DIR / self.user.terminal_id / self.prev_ema_file)
        if path.exists():
            with open(path, "r") as f:
                latest_record = f.read().split("\n")[-2]
                sent_flag = True if latest_record.split(",")[1] == "True" else False
                return datetime.strptime(latest_record.split(",")[0], '%Y%m%d%H%M%S'), sent_flag
        else:
            # まだEMAをとっていないときは今日の日付とFalseを返す. 起床は当日だけの話なので、前日以前しか記録がない時点でだめなので.
            return datetime.today(), False


class WakeLogic(Logic):
    def __init__(self, logger, postcode):
        super(WakeLogic, self).__init__(logger)
        self.postcode = postcode

    def __call__(self, answer_df, interrupt_df, *args, **kwargs):

        # 土日かつ天気がいい場合、お出かけしましょうのメッセージ
        weather = get_weather_info(self.postcode)
        today = datetime.today()
        if (datetime.weekday(today) >= 5 or jpholiday.is_holiday_name(
                today.date())) and "晴" in weather:
            return "woke_up"
        else:
            return "none"


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)
    logger.info("wake JITAI started.")
    prev_ema_date_file = "prev_ema_wake.txt"

    for index, user_info in const.USER_LIST.iterrows():
        jitai = Wake(user_info, logger, prev_ema_date_file)
        # emaの更新があり、かつ5時から10時の間であるか確認する. 条件を満たしたときはjitai.prev_ema_dateの更新も行う.
        if jitai.check_ema():
            logger.info("machine id: {} will be intervened.".format(jitai.user.terminal_id))
            jitai()
            # 最新EMA時間の保存
            if Path(const.DATA_DIR / jitai.user.terminal_id / "answer.csv").exists():
                with open(Path(const.DATA_DIR / jitai.user.terminal_id / prev_ema_date_file), "w") as f:
                    f.write(jitai.prev_ema_date.strftime('%Y%m%d%H%M%S') + ",True\n")
