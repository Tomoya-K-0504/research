import sys
from pathlib import Path

import yaml
from jitai.config import const
from jitai.config import logger as logger_file
from jitai.events.Intervene import Intervene
from jitai.src.EmaRecorder import EmaRecorder
from jitai.src.Pipeline import Pipeline
from jitai.src.User import User
from jitai.src.utils import import_events


if __name__ == "__main__":

    for index, user_info in const.USER_LIST.iterrows():
        user_data_dir = const.DATA_DIR / user_info["terminal_id"]
        for history_file in user_data_dir.iterdir():
            history_file.unlink()
