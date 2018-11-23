import re
import sys
import time
import json
from datetime import timedelta
from pathlib import Path

import const
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import logger


def access_site(url):
    # スクレイピング先のサーバーに負荷がかかりすぎないよう、0.5秒おく
    # time.sleep(0.5)
    html = requests.get(url).content
    soup = BeautifulSoup(html, "lxml")

    return html, soup


class JmaScraper:
    def __init__(self, pref, year="", month="", day="", prec_no="", block_no="", mode='daily'):
        self.pref = pref
        self.year = year
        self.month = month
        self.day = day
        self.prec_no = prec_no      # 県ごとにつけられる番号
        self.block_no = block_no    # 観測点ごとにつけられる番号
        self.mode = "daily"         # 日毎か時間毎か
        self._fill_prec_no(self)    # 県名からprec_noを補完する
        self.pref_select_page_url = f"http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?prec_no={self.prec_no}"
        self._fill_block_no(self)   # block_noを補完する


    @staticmethod
    def _update_base_url(self) -> None:
        """
        self.modeやself.dayを変更したときに、アクセスすべきURLを更新する.
        :return: None
        """
        self.base_url = f"http://www.data.jma.go.jp/obd/stats/etrn/view/{self.mode}_s1.php?prec_no={self.prec_no}&block_no={self.block_no}&year={self.year}&month={self.month}&day={self.day}&view=p1"

    @staticmethod
    def _fill_prec_no(self) -> None:
        """
        __init__で与えられた県名で、prec_noを検索して代入する
        :return: None
        """
        pref_code_df = self._load_pref_code()
        if self.pref == "北海道":  # 北海道のときは、札幌を観測点とするために、札幌がある地域の番号をprec_noとする
            self.prec_no = 14
        else:
            self.prec_no = pref_code_df[pref_code_df["pref"] == self.pref]["code"].values[0]

    @staticmethod
    def _fill_block_no(self) -> None:
        # その県の大きい観測所のhtml attributeを取得
        points = self.search_observatory()

        # なぜかpointsが2つずつ被りがあるので、block_noを取得して一位にする
        block_no_list = self._get_block_no(self, points)

        # 複数あるblock_noのうち、天気が取れているblockを採用してdfに格納する
        for block_no in block_no_list:
            self.block_no = block_no
            break

    @staticmethod
    def _load_pref_code():
        """
        気象庁の天気情報で県ごとに割り当てられているコードをcsvで保存し、保存されていれば読み込む。
        :return: dataframeで、カラムに 県名,code を持つ
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
        pref_code_df.to_csv("pref_code.csv", index=False)

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

            # 天気に関する情報が少ない場合a, 多い場合sとするルールがあるため、aの観測所は除く
            if point["onmouseover"].split(",")[0][-2] == 'a':
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

        df = self._extract_df_from_html(self)

        # スクレイピングが正常に行えていないときにストップするため.
        assert not df.empty

        return df


def zip2geo_api3(postal):
    url = "http://geoapi.heartrails.com/api/xml?method=searchByPostal&postal="

    content = json.loads(requests.get(f"{url}{str(postal).zfill(7)}").text)
    return content["results"][0]["address1"]


def zip2geo_api2(postal):
    url = "http://zipcloud.ibsnet.co.jp/api/search?zipcode="
    _ = f"{url}{str(postal).zfill(7)}"
    content = json.loads(requests.get(f"{url}{str(postal).zfill(7)}").text)
    return content["results"][0]["address1"]

def zip2geo(postal_list, pref_list):
    def refer_jp_post(postal):
        """

        :param postal:
        res['postal'], res['prefecture'], res['city'], res['town'], res['y'], res['x']
        :return: 6570805, 兵庫県, 神戸市灘区, 青谷町一丁目, 34.712429, 135.214521
        """
        if postal in postal_list:
            index = postal_list.index(postal)
        else:
            print(f"postcode {postal} is not in jp_post postcode list.")
            sys.exit(1)
        if len(index) == 0:
            print(f"postcode {postal} is in jp_post postcode list, but cannot get index")
            sys.exit(1)
        return pref_list[index]

    return refer_jp_post

        # 以下は一旦使用しない。多くアクセスすると切られるので。
        # url = 'http://zip.cgis.biz/csv/zip.php?zn='
        #
        # # 北海道などは0から郵便番号が始まり、おそらくexcelの仕様的に初めの0を消してしまうので、7桁になるよう0を先頭から埋める
        # try:
        #     content = requests.get(f"{url}{str(postal).zfill(7)}").text
        #     # decodeした結果がstr型で、xmlでパースがなぜかできなかったので、改行でsplitして県名が入った部分を取り出し、県名のみ切り出す
        #     pref_name = content.split("\",\"")[12]
        # except requests.exceptions.ConnectionError as e:
        #     print(e)
        #     try:
        #         pref_name = zip2geo_api2(postal)
        #     except TypeError as te:
        #         print(te)
        #         time.sleep(1800)
        #         pref_name = zip2geo1(postal)


def not_on_zipcode_list(source_df):
    df = pd.read_csv(Path(__file__).parent.resolve() / "KEN_ALL.CSV", encoding='shift-jis')
    postcode_list = list(set(df.iloc[:, 2].values))
    pref = df.iloc[:, 6]

    source_postcode = list(set(source_df["zip"].fillna(0).astype(int).values))

    with open("not_on_zipcode_list.txt", "w") as f:
        for one_postcode in source_postcode:
            if one_postcode not in postcode_list:
                if one_postcode == 0:
                    continue
                f.write(str(one_postcode))
                f.write("\n")
    pass


def zip2weather(refer_jp_postal, postcode, sdate, edate, mode='daily', duration=0):
    # pref_name = zip2geo1(postcode)

    pref_name = refer_jp_postal(postcode)

    # 日毎では、日付の指定がありdurationを考慮する必要がない.
    if mode == 'daily':
        daily_columns = ["temperature_mean", "temperature_max", "temperature_min", "humidity_mean", "weather_noon",
                         "weather_night"]
        start_daily_df = JmaScraper(pref_name, year=sdate.year, month=sdate.month, day=sdate.day).scrape()
        end_daily_df = JmaScraper(pref_name, year=edate.year, month=edate.month, day=edate.day).scrape()

        # 該当する日付の行を抜き出し、カラム名を変更する
        start_day_series = start_daily_df[start_daily_df["day"] == str(sdate.day)][daily_columns]
        start_day_series.columns = [f"s_{col}" for col in start_day_series.columns]
        end_day_series = end_daily_df[end_daily_df["day"] == str(edate.day)][daily_columns]
        end_day_series.columns = [f"e_{col}" for col in end_day_series.columns]

        # 連結して返す
        daily_series = pd.concat([start_day_series.reset_index(drop=True), end_day_series.reset_index(drop=True)], axis=1)
        return daily_series

    # dailyでないとき、つまりhourlyのとき
    hourly_df_list = []
    for date in [sdate, edate]:
        jma_scraper = JmaScraper(pref_name, year=date.year, month=date.month, day=date.day)
        hourly_df = pd.DataFrame()

        for i in range(duration*-1, duration+1):
            changed_date = date + timedelta(days=i)
            oneday_df = jma_scraper.scrape(mode='hourly', day=changed_date.day).reset_index(drop=True)
            hourly_df = pd.concat([hourly_df, oneday_df], axis=0)

        hourly_df_list.append(hourly_df)

    return hourly_df_list


if __name__ == "__main__":

    excel_name = sys.argv[1]

    # エクセルデータ
    source_df = pd.read_excel(excel_name)
    aggregated_df = pd.DataFrame()

    # 郵便局の住所に載っていない郵便番号を振り分けるのに使用した。
    # not_on_zipcode_list(source_df)
    with open("not_on_zipcode_list.txt") as f:
        not_on_zipcode_list = f.read().split("\n")[:-1]
    not_on_zipcode_list = [int(zipcode) for zipcode in not_on_zipcode_list]

    df = pd.read_csv(Path(__file__).parent.resolve() / "KEN_ALL.CSV", encoding='shift-jis')
    postcode_list = list(set(df.iloc[:, 2].values))
    pref_list = df.iloc[:, 6].values
    refer_jp_postal = zip2geo(postcode_list, pref_list)

    # 各データごとに、開始日の天気と終了日の天気をスクレイピングする
    for i, row in source_df.iterrows():

        save_folder = Path("weather_data") / row["folder"]
        save_folder.mkdir(exist_ok=True, parents=True)

        if len(list(save_folder.iterdir())) != 0:
            continue

        if int(row["zip"]) in not_on_zipcode_list:
            continue

        pref = row
        start_df, end_df = zip2weather(refer_jp_postal, int(row["zip"]), row["sday"], row["eday"], mode='hourly', duration=1)
        start_df.to_csv(save_folder / "start.csv", index=False)
        end_df.to_csv(save_folder / "end.csv", index=False)

        daily_df = zip2weather(refer_jp_postal, int(row["zip"]), row["sday"], row["eday"], mode='daily')
        aggregated_df = pd.concat([aggregated_df, daily_df], axis=0)

        if i % 100 == 0:
            print(f"{i} data finished")

    aggregated_df = pd.concat([source_df, aggregated_df.reset_index(drop=True)], axis=1)
    pass
