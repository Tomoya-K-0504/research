import argparse
import sys
import os
from logging import getLogger, INFO, DEBUG, ERROR, FileHandler, StreamHandler, Formatter


def logger(log_folder="./logs"):

    if not os.path.exists(log_folder):
        os.mkdir(log_folder)

    logger = getLogger()
    logger.setLevel(INFO)
    formatter = Formatter(
        fmt='%(threadName)s: %(asctime)-15s: %(pathname)s:l-%(lineno)d:\n\t[%(levelname)s] %(message)s')

    error_handler = FileHandler(filename=f"{log_folder}/ERROR.log")
    error_handler.setLevel(ERROR)
    error_handler.setFormatter(fmt=formatter)
    logger.addHandler(error_handler)

    debug_handler = FileHandler(filename=f"{log_folder}/DEBUG.log")
    debug_handler.setLevel(DEBUG)
    debug_handler.setFormatter(fmt=formatter)
    logger.addHandler(debug_handler)

    info_handler = FileHandler(filename=f"{log_folder}/INFO.log")
    info_handler.setLevel(INFO)
    info_handler.setFormatter(fmt=formatter)
    logger.addHandler(info_handler)

    stream_info_handler = StreamHandler(stream=sys.stdout)
    stream_info_handler.setLevel(INFO)
    stream_info_handler.setFormatter(fmt=formatter)
    logger.addHandler(stream_info_handler)

    return logger
