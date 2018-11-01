import os, time, re, math
import requests
import pandas as pd
import sys
from bs4 import BeautifulSoup
from pathlib import Path
import json

import requests
from bs4 import BeautifulSoup


def access_site(url):
    html = requests.get(url).content
    soup = BeautifulSoup(html, "lxml")

    return html, soup


class JmaScraper:
    def __init__(self, geo_data, year="", month="", day="", prec_no="", block_no=""):
        self.postal = geo_data["postal"]
        self.pref = geo_data["prefecture"]
        self.city = geo_data['city']
        self.town = geo_data['town']
        self.longitude = float(geo_data["x"])
        self.latitude = float(geo_data["y"])
        self.year = year
        self.month = month
        self.day = day
        self.prec_no = prec_no
        self.block_no = block_no
        # self.html, self.soup = access_site(self.base_url)
        self._fill_prec_no(self)
        self.pref_select_page_url = f"http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?prec_no={self.prec_no}"

    @staticmethod
    def _update_base_url(self):
        self.base_url = f"http://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php?prec_no={self.prec_no}&block_no={self.block_no}&year={self.year}&month={self.month}&day={self.day}&view=a2"

    @staticmethod
    def _fill_prec_no(self):
        """
        __init__で与えられた県名で、prec_noを検索して代入する
        :return:
        """
        pref_code_df = self._load_pref_code()
        self.prec_no = pref_code_df[pref_code_df["pref"] == self.pref]["code"].values[0]

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
        # TODO 北海道の地方名をどうするか. 未対応

        columns_dict = {"pref": "", "code": 0}
        pref_code_df = pd.DataFrame(columns=columns_dict.keys())
        for point in points:
            columns_dict["code"] = [int(re.search("\d\d", point["href"]).group())]
            columns_dict["pref"] = [point["alt"]]
            _ = pd.DataFrame.from_dict(columns_dict)
            pref_code_df = pd.concat([pref_code_df, pd.DataFrame.from_dict(columns_dict)], axis=0)
        pref_code_df.to_csv("pref_code.csv")

        return pref_code_df

    @staticmethod
    def _scrape_table(self, soup):
        # htmlソースからレース結果のテーブルを探してくる
        table = soup.find("table", class_="data2_s")

        df = pd.read_html(table.prettify(), header=0)[0]

        return df

    def search_nearest_block(self):
        self._update_base_url(self)
        html, soup = access_site(self.pref_select_page_url)
        all_points = soup.find_all("area")

        nearest_point = all_points[0]
        nearest_distance = self._calc_distance(self, nearest_point)
        for point in all_points:
            if "onmouseover" not in point.attrs.keys():
                continue
            distance = self._calc_distance(self, point)
            if distance < nearest_distance:
                nearest_point = point
                nearest_distance = distance

        return nearest_point

    @staticmethod
    def _calc_distance(self, point):
        try:
            lat = float(point["onmouseover"].split(",")[4][1:-1]) + float(point["onmouseover"].split(",")[5][1:-1]) / 60
            lon = float(point["onmouseover"].split(",")[6][1:-1]) + float(point["onmouseover"].split(",")[7][1:-1]) / 60
        except KeyError as e:
            print(point)
            sys.exit(1)
        return math.sqrt((lat - self.latitude) ** 2 + (lon - self.longitude) ** 2)

    def scrape(self):
        point = self.search_nearest_block()

        self.block_no = point["href"].split("block_no=")[1].split("&")[0]
        self._update_base_url(self)
        html, soup = access_site(self.base_url)

        df = self._scrape_table(self, soup)
        return df


def zip2geo(postal):
    """

    :param postal:
    res['postal'], res['prefecture'], res['city'], res['town'], res['y'], res['x']
    :return: 6570805, 兵庫県, 神戸市灘区, 青谷町一丁目, 34.712429, 135.214521
    """
    url = 'http://geoapi.heartrails.com/api/json'
    payload = {'method': 'searchByPostal'}
    payload['postal'] = '657-0805'

    res = requests.get(url, params=payload).json()['response']['location'][0]
    print('%s, %s, %s, %s, %s, %s\n' % (res['postal'], res['prefecture'], res['city'], res['town'], res['y'], res['x']))

    return res


if __name__ == "__main__":

    postcode = "657-0026"
    get_data = zip2geo(postcode)
    jma_scraper = JmaScraper(get_data, year=2018, month=10, day=10)
    df = jma_scraper.scrape()

    pass
