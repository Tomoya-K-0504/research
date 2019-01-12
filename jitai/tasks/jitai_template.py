from datetime import datetime, timedelta
from pathlib import Path

import jpholiday
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.src.Dams import Dams
from jitai.src.Intervene import Intervene
from jitai.src.Jitai import Jitai
from jitai.src.LivedoorApi import get_weather_info
from jitai.src.Logic import Logic
from jitai.src.utils import get_token


class EveryMinute(Jitai):
    def __init__(self, terminal_id, logger, prev_ema_file):
        super(EveryMinute, self).__init__(terminal_id, logger, prev_ema_file)

    def __call__(self, *args, **kwargs) -> None:
        logic = TemplateLogic(self.logger)
        super.__call__(logic=logic)

    # 読み込み方と初回の挙動を記述
    def _load_prev_ema(self) -> datetime:
        path = Path(const.DATA_DIR / self.user.terminal_id / self.prev_ema_file)
        if path.exists():
            with open(path, "r") as f:
                return datetime.strptime(f.read().split("\n")[-2], '%Y%m%d%H%M%S')
        else:
            # 一回目は30日分をとってくる
            return datetime.today() - timedelta(days=30)

    def check_ema(self) -> bool:
        self.prev_ema_date = self._load_prev_ema()

        # 今回の更新分をとってくる
        answer_df, interrupt_df, timeout_df = self.ema_recorder(self.prev_ema_date.date().strftime('%Y%m%d'),
                                                                datetime.today().date().strftime('%Y%m%d'),
                                                                save_df=True)

        # answer_dfがないときとは、初回でかつEMAの記録がないときで、prev_ema_timeとanswer_dfの終了時間が同じときとは、EMAの記録があるが更新がないとき
        if len(answer_df) == 0 or self.prev_ema_date == datetime.strptime(answer_df["end"].values[-1][:-4],
                                                                          '%Y/%m/%d %H:%M:%S'):
            return False

        # prev_ema_dateの更新
        self.prev_ema_date = datetime.strptime(answer_df["end"].values[-1][:-4], '%Y/%m/%d %H:%M:%S')

        # TODO 時間まで指定できるようになったらこれでよい
        # return bool(len(answer_df))

        return True


class TemplateLogic(Logic):
    def __init__(self, logger):
        super(TemplateLogic, self).__init__(logger)

    def __call__(self, answer_df, interrupt_df, *args, **kwargs) -> str:
        # 以下を変更する. 返り値はconst.pyのINTERRUPT_MSGのkey名

        index_list = list(set(answer_df.index))

        # 土日かつ天気がいい場合、お出かけしましょうのメッセージ
        weather = get_weather_info("神戸")
        today = datetime.today()
        if (datetime.weekday(today) >= 4 or jpholiday.is_holiday_name(
                today.date())) and "晴" in weather or "曇" in weather:
            return "off_day_go_outside"

        # DAMSによる心理状態の把握
        answer_df["ema_id"] = answer_df.index
        answer_df.reset_index(inplace=True, drop=True)
        dams = Dams(answer_df[answer_df["ema_id"] == index_list[-1]])
        dams_thresh = 200

        # anxietyが200を超えると、「不安ですか？」
        if dams.anxiety >= dams_thresh:
            return "anxiety"

        # depressiveが200を超えると、「憂鬱ですか？」
        if dams.depressive >= dams_thresh:
            return "depressive"

        # positiveが200を超えると、「いい調子です！」
        if dams.positive >= dams_thresh:
            return "positive"

        # positiveが200を超えると、「気持ちが消極的ですか?」
        if dams.negative >= dams_thresh:
            return "negative"

        # "眠い"が75を超えたら、気分転換に散歩はどうですかメッセージ
        times_answered = list(set(answer_df.index))
        if len(answer_df) >= 1 and answer_df[answer_df["question"] == "眠い"].loc[times_answered[-1], "answer"] > 75:
            return "sleepy"

        # 3回以上"疲れた"が70を超えていたら、お疲れですかのメッセージ
        elif len(answer_df) >= 3 and sum(
                answer_df[answer_df["question"] == "疲れた"].loc[times_answered[-3:], "answer"] > 70) == 3:
            return "fatigue"

        else:
            return "none"


if __name__ == "__main__":
    logger = logger_file.logger(const.LOG_DIR)
    logger.info("every minute JITAI started.")
    prev_ema_file = "prev_ema_date.txt"

    for index, user_info in const.USER_LIST.iterrows():
        jitai = EveryMinute(user_info, logger, prev_ema_file)
        if jitai.check_ema():
            logger.info("machine id: {} will be intervened.".format(jitai.user.terminal_id))
            jitai()
        # 保存されたEMAがある場合、最新EMA時間の保存
        if Path(const.DATA_DIR / jitai.user.terminal_id / "answer.csv").exists():
            with open(Path(const.DATA_DIR / jitai.user.terminal_id / "prev_ema_date.txt"), "w") as f:
                f.write(jitai.prev_ema_date.strftime('%Y%m%d%H%M%S') + "\n")
