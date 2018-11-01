import os, time, re
import requests
import pandas as pd
import sys
from bs4 import BeautifulSoup
from pathlib import Path
import json

import requests
from bs4 import BeautifulSoup


def zip2geo(postcode):
    """
    郵便番号を引数として、緯度と経度を返す.参考サイト→https://renztech.wordpress.com/2018/02/28/%E9%83%B5%E4%BE%BF%E7%95%AA%E5%8F%B7%E3%82%92%E7%B7%AF%E5%BA%A6%E7%B5%8C%E5%BA%A6%E3%81%AB%E5%A4%89%E6%8F%9B%E3%81%99%E3%82%8B/
    :param postcode: 7桁の数字(str)で、ハイフン可
    :return: 緯度と経度
    """
    # ハイフンを除く
    postcode = postcode.replace("-", "")

    zip2geo_df = pd.read_csv("./Zip2Geoc.csv")
    (longitude, latitude) = zip2geo_df[zip2geo_df["Zip"] == int(postcode)][["Lon", "Lat"]].values[0]

    return (longitude, latitude)


def access_site(url):
    html = requests.get(url).content
    soup = BeautifulSoup(html, "lxml")

    return html, soup


class JmaScraper:
    def __init__(self, year=2010, month=1, day=1):
        self.year = year
        self.month = month
        self.day = day
        self.base_url = f"http://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?prec_no=44&block_no=47662&year={self.year}&month={self.month}&day={self.day}&view=a2"

        self.html = requests.get(self.base_url).content
        self.soup = BeautifulSoup(self.html, "lxml")
        self.pref_code_df = self._load_pref_code()

    @staticmethod
    def _read_table(self):
        # htmlソースからレース結果のテーブルを探してくる
        table = self.soup.find("table", class_="data2_s")

        df = pd.read_html(table.prettify(), header=0)

    @staticmethod
    def _load_pref_code():
        """
        気象庁の天気情報で県ごとに割り当てられているコードをcsvで保存し、保存されていれば読み込む。
        :return: dataframeで、カラムに 県名 code を持つ
        """
        if Path("pref_code.csv").exists():
            return pd.read_csv("pref_code.csv")

        url = "http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture00.php"
        html, soup = access_site(url)
        points = soup.find_all("area")
        # TODO 北海道の地方名をどうするか

        columns_dict = {"pref": "", "code": 0}
        pref_code_df = pd.DataFrame(columns=columns_dict.keys())
        for point in points:
            columns_dict["code"] = [int(re.search("\d\d", point["href"]).group())]
            columns_dict["pref"] = [point["alt"]]
            _ = pd.DataFrame.from_dict(columns_dict)
            pref_code_df = pd.concat([pref_code_df, pd.DataFrame.from_dict(columns_dict)], axis=0)
        pref_code_df.to_csv("pref_code.csv")

        return pref_code_df


if __name__ == "__main__":

    # URLで年と月ごとの設定ができるので%sで指定した英数字を埋め込めるようにします。
    postcode = "657-0026"
    jma_scraper = JmaScraper()
    longitude, latitude = zip2geo(postcode)

    pass
