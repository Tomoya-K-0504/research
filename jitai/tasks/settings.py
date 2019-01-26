import sys
from pathlib import Path
from datetime import datetime
import pd

import yaml
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.events.Intervene import Intervene
from jitai.src.EmaRecorder import EmaRecorder
from jitai.src.Pipeline import Pipeline
from jitai.src.User import User
from jitai.src.utils import import_events, start_end_to_datetime

if __name__ == "__main__":

    # 一度行った介入については、介入Noごとにファイルを作成することで介入済みとし、毎日12時になったら
    # すべての介入済みファイルを削除してリセットする.

    logger = logger_file.logger(const.LOG_DIR)

    params_file = sys.argv[1]
    # param_files = [p.name for p in Path(const.PJ_ROOT / "yamls").iterdir() if p.name.startswith("n")]

    with open(const.PJ_ROOT / "yamls" / params_file) as f:
        params = yaml.load(f)

    for index, user_info in const.USER_LIST.iterrows():
        # 初めてEMA取得を行う場合にデータ保存フォルダを作成
        user_data_dir = const.DATA_DIR / user_info["terminal_id"]
        Path(user_data_dir / "intervene_history").mkdir(exist_ok=True, parents=True)

        steps = []

        ema = pd.read_csv(user_data_dir / "ema.csv")
        ema = start_end_to_datetime(ema)

        intervene = Intervene(params[-1], user_info, logger)

        # TODO useがfalseのときは、タプルの3要素目にfalseとかを入れる？

        for param in params[:-1]:
            suffix = ""
            if "use" not in param.keys():
                EventClass = import_events(param["event"])
                event_class = EventClass(param, ema, user_info, logger)
                if "depend" in param.keys():
                    # condition_nameがdependと一緒だったら、そのクラスをsuffixに追加する
                    suffix = [s[1] for s in steps if s[0] == param["depend"]][0]
                if "use" in param.keys():
                    suffix = False

                steps.append((param["condition_name"], event_class, suffix))
        pipeline = Pipeline(steps)
        answer = pipeline.run()
        if answer and not Path(user_data_dir / "intervene_history" / str(params_file[:-4]+".txt")).exists():
            logger.info("condition all true, intervene will occur.")
            intervene()
            with open(user_data_dir / "intervene_history" / str(params_file[:-4]+".txt"), "w") as f:
                f.write("")
