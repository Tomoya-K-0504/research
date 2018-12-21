import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


air_pressure_col = ["air_pressure_local", "air_pressure_sea"]

humidity_col = ["humidity_mean", "humidity_min"]

weather_col = ["weather_noon", "weather_night"]

daily_columns_s1 = ["day", *air_pressure_col, "precipitation_sum", "precipitation_hourly_max",
                    "precipitation_10min_max", "temperature_mean", "temperature_max", "temperature_min", *humidity_col,
                    "wind_speed_mean", "wind_speed_max", "wind_speed_max_direction",
                    "wind_instantaneous_speed_max", "wind_instantaneous_speed_direction", "day_length", "snow_sum",
                    "snow_max_depth", *weather_col]

hourly_columns_s1 = ["hour", *air_pressure_col, "precipitation", "temperature", "dew_point_temperature",
                     "vapor_pressure", "humidity", "wind_speed", "wind_direction", "day_length",
                     "globa_solar_radiation", "snow_fall", "fallen_snow", "weather", "cloud_cover", "visibility"]


def access_site(url):
    # スクレイピング先のサーバーに負荷がかかりすぎないよう、0.5秒おく
    # time.sleep(0.5)
    html = requests.get(url).content
    soup = BeautifulSoup(html, "lxml")

    return html, soup


class JmaScraper:
    def __init__(self, pref, year="", month="", day="", prec_no="", block_no="", mode='daily'):
        """
        気象庁の過去の天気ページをスクレイピングするためのクラス
        :param pref: 県名. 都道府県までつける.
        :param year: yyyyで
        :param month: mmで、04 等
        :param day: ddで、04 等
        :param prec_no: 天気サイト内で使われる、都道府県に対して振られるID. 北海道は地域ごとなので注意
        :param block_no: 各都道府県内の観測点に振られているID.
        :param mode: 'daily'と'hourly'がある. 日毎か1時間毎かを決める.
        """
        self.pref = pref
        self.year = year
        self.month = month
        self.day = day
        self.prec_no = prec_no
        self.block_no = block_no
        self.mode = "daily"
        self.pref_select_page_url = f"http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?prec_no="
        self._fill_prec_block_no(self)    # 県名からprec_noとblock_noを補完する
        # self._fill_block_no(self)   # 途中でblock_noを変更する

    def __call__(self, *args, **kwargs):
        return self.scrape()

    @staticmethod
    def _update_base_url(self, **kwargs) -> None:
        """
        self.modeやself.dayを変更したときに、アクセスすべきURLを更新する.
        :return: None
        """
        if "mode" in kwargs.keys():
            self.base_url = f"http://www.data.jma.go.jp/obd/stats/etrn/view/{kwargs['mode']}_s1.php?prec_no={kwargs['prec_no']}&block_no={kwargs['block_no']}&year={kwargs['year']}&month={kwargs['month']}&day={kwargs['day']}&view=p1"
        else:
            self.base_url = f"http://www.data.jma.go.jp/obd/stats/etrn/view/{self.mode}_s1.php?prec_no={self.prec_no}&block_no={self.block_no}&year={self.year}&month={self.month}&day={self.day}&view=p1"

    @staticmethod
    def _fill_prec_block_no(self) -> None:
        """
        __init__で与えられた県名で、prec_noを検索して代入する
        :return: None
        """
        pref_code_df = self._load_pref_block_code(self)
        if self.pref == "北海道":  # 北海道のときは、札幌を観測点とするために、札幌がある地域の番号をprec_noとする
            self.prec_no = 14
            self.block_no = 47412
        else:
            self.prec_no = pref_code_df[pref_code_df["pref"] == self.pref]["prec_no"].values[0]
            self.block_no = int(pref_code_df[pref_code_df["pref"] == self.pref]["block_no"].values[0])

    @staticmethod
    def _load_pref_block_code(self):
        """
        気象庁の天気情報で県ごとに割り当てられているコードをcsvで保存する. 保存されていれば読み込んで返す
        :return: dataframeで、カラムに 県名,code を持つ
        """
        if Path("prec_block_code.csv").exists():
            return pd.read_csv("prec_block_code.csv")

        url = "http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture00.php"
        html, soup = access_site(url)
        points = soup.find_all("area")
        # TODO 北海道の地方名をどうするか. 未対応

        columns_dict = dict.fromkeys(["pref", "prec_no", "block_no"])
        prec_block_no_df = pd.DataFrame(columns=columns_dict.keys())
        for point in points:
            columns_dict["pref"] = [point["alt"]]
            columns_dict["prec_no"] = [int(re.search("\d\d", point["href"]).group())]
            columns_dict["block_no"] = [self._find_block_no(self, columns_dict["prec_no"][0])]
            prec_block_no_df = pd.concat([prec_block_no_df, pd.DataFrame.from_dict(columns_dict)], axis=0)
        prec_block_no_df.to_csv("prec_block_code.csv", index=False)

        return prec_block_no_df

    @staticmethod
    def _find_block_no(self, prec_no="0") -> None:
        """
        prec_noの都道府県の中で、天気を持つ地域のblock_noを見つけ出す
        :param prec_no: 都道府県ID
        :return: 地域のID
        """

        # その県の大きい観測所のhtml attributeを取得
        points = self.search_observatory(prec_no)

        # なぜかpointsが2つずつ被りがあるので、block_noを取得して一位にする
        block_no_list = self._get_block_no(points)

        # 複数あるblock_noのうち、天気が取れているblockを採用してdfに格納する
        for block_no in block_no_list:
            self.block_no = block_no
            kwargs = {"mode": "daily", "prec_no": str(prec_no), "block_no": str(block_no), "year": "2010", "month": "4", "day": "1"}
            self._update_base_url(self, **kwargs)
            # urlを更新して、ページにアクセス
            html, soup = access_site(self.base_url)
            df = self._scrape_table(soup)
            # もし最右下段、つまり天気がnanじゃなかったら、block_noを返却
            if not pd.isna(df.iloc[-1, -1]):
                return block_no

    def search_observatory(self, prec_no):
        """
        大きい観測点を検索して返す
        :return: 大きい観測点のsoupオブジェクトが入ったリスト
        """
        html, soup = access_site(self.pref_select_page_url + str(prec_no))
        all_points = soup.find_all("area")
        big_observatories = []

        for point in all_points:
            # このタグが付いていないページもある.
            if "onmouseover" not in point.attrs.keys():
                continue

            # 天気に関する情報が少ない場合a, 多い場合sとするルールがあるため、aの観測所は除く
            if point["onmouseover"].split(",")[0][-2] == 'a':
                continue

            if point["onmouseover"].split(",")[13][1:2] == '1':
                big_observatories.append(point)

        return big_observatories

    @staticmethod
    def _get_block_no(points):
        """
        地域IDをurlの中から抜き出す
        :param points: 各地点のsoupオブジェクトが入ったリスト
        :return: 各地点の地域IDのリスト
        """
        return list(set([point["href"].split("block_no=")[1].split("&")[0] for point in points]))

    @staticmethod
    def _scrape_table(soup, class_name="data2_s"):
        """
        htmlソースから天気のテーブルを探して返す
        :param soup: サイトのhtmlをsoup型に変更したもの
        :param class_name: html attributesのクラス名
        :return: 天気のテーブルが格納されたdataframe
        """
        table = soup.find("table", class_=class_name)
        df = pd.read_html(table.prettify(), header=0)[0]

        return df

    @staticmethod
    def _extract_df_from_html(self):
        """
        天気の一覧テーブルからdataframeを抽出し、整形して返す
        :param self: 自クラス
        :return: 天気一覧図のdataframe
        """
        self._update_base_url(self)
        time.sleep(0.5)
        html = requests.get(self.base_url).content
        soup = BeautifulSoup(html, "lxml")

        # スクレイプしたページから、テーブルをdataframeの形式で抽出する
        df = self._scrape_table(soup)

        if self.mode == "daily":
            df = df[3:]     # カラム名のところ
            df.columns = daily_columns_s1
        else:
            df = df[1:]     # カラム名のところ
            df.columns = hourly_columns_s1

        return df

    def scrape(self, **kwargs):
        """
        気象庁の天気webサイトから、スクレイピングする
        :param kwargs: 'day'と'mode'を用意している. クラスインスタンス作成後、dayの変更、modeの変更が可能になる
        :return: スクレイピングしたdf
        """

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


if __name__ == "__main__":
    from datetime import datetime
    today = datetime.today()
    start_daily_df = JmaScraper("大阪府", year=today.year, month=today.month, day=today.day).scrape()
    a = ""