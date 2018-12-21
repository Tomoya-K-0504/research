from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PJ_ROOT / "logs"
DATA_DIR = PJ_ROOT / "data"

BASE_URL = "osaka1.behi-lab.com"
API_URL = "api/v1"
MODE_URL = {"ema": "assessments", "interrupt": "notifications"}
HEADERS = {"Content-Type": "application/json"}

# MACHINE_ID = "5bee2c58d01c504d45e18cfc"   # 小池が借りている端末
MACHINE_ID = "5c1311c509a5e745750cdc0d"     # Dec. 14に一日だけ借りた端末
LOGIN_ID = "osaka.behi.lab@gmail.com"
PASSWORD = "osaka.behi.lab@gmail.com"


# 介入時のアラートは、ラベルと本文をセットで管理する
INTERRUPT_MSG = {
    "fatigue": {"title": "お疲れですか？", "body": "お疲れですか？ 少し休憩をとるのはいかがでしょう."},
    "sleepy": {"title": "眠いですか？", "body": "散歩してみるのはどうですか."},
    "none": {"title": "どうも", "body": "調子いいですか"}
}


