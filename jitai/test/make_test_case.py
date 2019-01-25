import pandas as pd
from jitai.tasks.sleep import Sleep, SleepLogic
from jitai.config import const
from jitai.config import logger as logger_file
from pathlib import Path


logger = logger_file.logger(const.LOG_DIR)

sleep_test_case_dir = Path("testcases") / "mother_wake"
sleep_test_case_dir.mkdir(exist_ok=True, parents=True)

# df, _, _ = Sleep(const.USER_LIST.iloc[2, :], logger, prev_ema_file).ema_recorder(from_date="", to_date="")
# df = df.applymap(lambda x: str(x).replace("\n", "").replace("\r", ""))
# df.to_csv(test_case_dir / "model_test_case.csv", sep=',')

df = pd.read_csv(sleep_test_case_dir / "model_test_case.csv", index_col=0)

pd.DataFrame(columns=df.columns).to_csv(sleep_test_case_dir / "no_ema.csv")

df.to_csv(sleep_test_case_dir / "ema__before_6_hours.csv")

df_last_not_sleep = df[df["event"] == "wake"]
df_last_not_sleep.to_csv(sleep_test_case_dir / "last_not_sleep.csv")

df_last_sleep = df[df["event"] == "sleep"]
df_last_sleep.to_csv(sleep_test_case_dir / "last_sleep.csv")