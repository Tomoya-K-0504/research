import os
from pathlib import Path
from jitai.config import const


test_files = list(Path(const.PJ_ROOT / "test").iterdir())
test_files = [p for p in test_files if p.name.startswith("t") and p.name.endswith("y")]

for test_path in test_files:
    os.chdir(const.PJ_ROOT / "test")
    os.system("/Users/koiketomoya/.pyenv/versions/anaconda3-5.1.0/envs/research/bin/python -m unittest {}".format(test_path.name))
