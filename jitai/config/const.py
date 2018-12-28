from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PJ_ROOT / "logs"
DATA_DIR = PJ_ROOT / "data"

BASE_URL = ""
API_URL = ""
MODE_URL = {}
HEADERS = {}

MACHINE_ID = ""
LOGIN_ID = ""
PASSWORD = ""


# 介入時のアラートは、ラベルと本文をセットで管理する
INTERRUPT_MSG = {
    "fatigue": {"title": "お疲れですか？", "body": "お疲れですか？ 少し休憩をとるのはいかがでしょう."},
    "sleepy": {"title": "眠いですか？", "body": "散歩してみるのはどうですか."},
    "off_day_go_outside": {"title": "天気の良い休日です!", "body": "外へ出かけましょう!"},
    "none": {"title": "どうも", "body": "調子いいですか"}
}


