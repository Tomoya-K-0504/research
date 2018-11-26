手順書とデータ構造について記載する

ソースコードをクローンする
```
git clone https://github.com/Tomoya-K-0504/research.git
cd research/weather
```

pythonの仮想環境を作成する。anacondaを使う場合を記載する。
```
conda -V # condaが使えることを確認
conda create -n research python=3.6
```

必要なライブラリをインストールする
```
pip install -r requirements.txt

```

実行
```
source activate research
cd research/weather
python zip2weather.py
```