import os, time, re, math
import requests
import pandas as pd
import sys
from bs4 import BeautifulSoup
from pathlib import Path
import json

import requests
from bs4 import BeautifulSoup

import const


def access_site(url):
    time.sleep(0.5)
    html = requests.get(url).content
    soup = BeautifulSoup(html, "lxml")

    return html, soup


class JmaScraper:
    def __init__(self, pref, year="", month="", day="", prec_no="", block_no="", mode='daily'):
        self.pref = pref
        self.year = year
        self.month = month
        self.day = day
        self.prec_no = prec_no # 県ごとにつけられる番号
        self.block_no = block_no
        self.mode = "daily"
        # self.html, self.soup = access_site(self.base_url)
        self._fill_prec_no(self)
        self.pref_select_page_url = f"http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?prec_no={self.prec_no}"

    @staticmethod
    def _update_base_url(self, unknown="s1"):
        self.base_url = f"http://www.data.jma.go.jp/obd/stats/etrn/view/{self.mode}_s1.php?prec_no={self.prec_no}&block_no={self.block_no}&year={self.year}&month={self.month}&day={self.day}&view=p1"

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
    def _scrape_table(self, soup, class_name="data2_s"):
        # htmlソースからレース結果のテーブルを探してくる
        table = soup.find("table", class_=class_name)

        df = pd.read_html(table.prettify(), header=0)[0]

        return df

    def search_observatory(self):
        self._update_base_url(self)
        html, soup = access_site(self.pref_select_page_url)
        all_points = soup.find_all("area")
        big_observatories = []

        for point in all_points:
            if "onmouseover" not in point.attrs.keys():
                continue

            if point["onmouseover"].split(",")[13][1:2] == '1':
                big_observatories.append(point)

        return big_observatories

    @staticmethod
    def _get_block_no(self, points):
        return list(set([point["href"].split("block_no=")[1].split("&")[0] for point in points]))

    @staticmethod
    def _extract_df_from_html(self):
        self._update_base_url(self)
        html, soup = access_site(self.base_url)

        # スクレイプしたページから、テーブルをdataframeの形式で抽出する
        df = self._scrape_table(self, soup)

        if self.mode == "daily":
            df = df[3:]
            df.columns = const.daily_columns_s1
        else:
            df = df[1:]
            df.columns = const.hourly_columns_s1

        return df

    def scrape(self, **kwargs):

        # dayとmodeをscrapeから変えられるようにしておく
        if "day" in kwargs.keys():
            self.day = kwargs["day"]
        if "mode" in kwargs.keys():
            self.mode = kwargs["mode"]
        self._update_base_url(self)

        # 天気があるblock_noを取得できているならば、あとはdfを取得するだけ.
        if self.block_no:
            df = self._extract_df_from_html(self)

        else:
            # その県の大きい観測所のhtml attributeを取得
            points = self.search_observatory()

            # なぜかpointsが2つずつ被りがあるので、block_noを取得して一位にする
            block_no_list = self._get_block_no(self, points)

            # 複数あるblock_noのうち、天気が取れているblockを採用してdfに格納する
            for block_no in block_no_list:
                self.block_no = block_no
                df = self._extract_df_from_html(self)

                # 天気の列に値があればbreakでfor文終了
                if not df["weather_noon"].isnull().all():
                    break

        return df


def zip2geo(postal):
    """

    :param postal:
    res['postal'], res['prefecture'], res['city'], res['town'], res['y'], res['x']
    :return: 6570805, 兵庫県, 神戸市灘区, 青谷町一丁目, 34.712429, 135.214521
    """
    url = 'http://geoapi.heartrails.com/api/json'
    payload = {'method': 'searchByPostal'}
    payload['postal'] = postal

    res = requests.get(url, params=payload).json()['response']['location'][0]
    print('%s, %s, %s, %s, %s, %s\n' % (res['postal'], res['prefecture'], res['city'], res['town'], res['y'], res['x']))

    return res


def zip2weather(postcode):
    get_data = zip2geo(postcode)

    jma_scraper = JmaScraper(get_data["prefecture"], year=2018, month=10, day=10, mode='daily')
    daily_df = jma_scraper.scrape(mode='daily')

    hour_allday_df = pd.DataFrame()
    # 1日ごとに一行化と連結処理を行っていく
    for day in range(1, len(daily_df)+1):
        oneday_hour_series = pd.Series()
        hourly_df = jma_scraper.scrape(mode='hourly', day=day).reset_index(drop=True)
        hourly_df.set_index("hour", inplace=True)
        for hour, row in hourly_df.iterrows():
            row.index = [f"{col}_{hour}" for col in hourly_df.columns]
            oneday_hour_series = pd.concat([oneday_hour_series, row])
        # TODO 1日目のすべてのカラム、2日目のすべてのカラム、という順場になるように、カラムのsortをfalseにする
        hour_allday_df = pd.concat([hour_allday_df, oneday_hour_series], axis=1)
    hour_allday_df.columns = list(daily_df.index)
    _ = hour_allday_df.T
    master = pd.concat([daily_df, hour_allday_df.T], axis=1)
    pass


if __name__ == "__main__":

    postcode = "453-0061"
    zip2weather(postcode)

    pass
