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
        html, soup = access_site(self.base_url)

        # スクレイプしたページから、テーブルをdataframeの形式で抽出する
        df = self._scrape_table(soup)

        if self.mode == "daily":
            df = df[3:]     # カラム名のところ
            df.columns = const.daily_columns_s1
        else:
            df = df[1:]     # カラム名のところ
            df.columns = const.hourly_columns_s1

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


def refer_jp_post(postal, postal_list, pref_list):
    """
    郵便局が提供しているcsvを使って、郵便番号と都道府県名を取得し、引数に該当する都道府県名を返す
    :param postal:
    res['postal'], res['prefecture'], res['city'], res['town'], res['y'], res['x']
    :return: 6570805, 兵庫県, 神戸市灘区, 青谷町一丁目, 34.712429, 135.214521
    """
    if postal in postal_list:
        index = postal_list.index(postal)
    else:
        print(f"postcode {postal} is not in jp_post postcode list.")
        sys.exit(1)

    return pref_list[index]


def not_on_zipcode_list(source_df):
    """
    郵便局のcsvに載っていない郵便番号をリスト化して保存する.
    :param source_df: 天気を収集したい郵便番号が入ったcsv
    :return: None
    """
    # 郵便局のcsvを読み込む
    df = pd.read_csv(Path(__file__).parent.resolve() / "KEN_ALL.CSV", encoding='shift-jis')
    postcode_list = list(set(df.iloc[:, 2].values))

    # 収集する郵便番号を一位にする. nanは0で埋め、後でスキップする
    source_postcode = list(set(source_df["zip"].fillna(0).astype(int).values))

    with open("not_on_zipcode_list.txt", "w") as f:
        for one_postcode in source_postcode:
            if one_postcode not in postcode_list:
                if one_postcode == 0:   # 0は空欄を埋めたところなのでスキップ
                    continue
                f.write(str(one_postcode))
                f.write("\n")


def zip2weather(pref_name, sdate, edate, mode='daily', duration=0):
    """
    郵便番号から天気を取得する
    :param pref_name: 県名
    :param sdate: 実験開始日
    :param edate: 実験終了日
    :param mode: 'daily'か'hourly'
    :param duration: 前後何日間か
    :return: daily_series.. , hourly_df_list..
    """

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

    input_excel_name = sys.argv[1]

    # エクセルデータ
    source_df = pd.read_excel(input_excel_name)
    aggregated_df = pd.DataFrame()

    # 郵便局の住所に載っていない郵便番号を振り分けるのに使用した。
    # not_on_zipcode_list(source_df)

    with open("not_on_zipcode_list.txt") as f:
        not_on_zipcode_list = f.read().split("\n")[:-1]
    not_on_zipcode_list = [int(zipcode) for zipcode in not_on_zipcode_list]

    # 郵便局の郵便番号リストを読み込む
    df = pd.read_csv(Path(__file__).parent.resolve() / "KEN_ALL.CSV", encoding='shift-jis')
    postcode_list = list(set(df.iloc[:, 2].values))
    pref_list = df.iloc[:, 6].values

    count_2 = 0

    # 既にスクレイプしたファイルリストを読み込む
    with open(Path("finished_list.txt"), "r") as f:
        finished_list = f.read().split("\n")[:-1]

    # 各データごとに、開始日の天気と終了日の天気をスクレイピングする
    for i, row in source_df.iterrows():

        # 既にスクレイプしたファイルリストに含まれていればスキップ
        # if row["folder"] in finished_list:
        #     continue

        # 元データに郵便番号がはいっていない場合 または 郵便局のデータに載っていないリストに郵便番号が入っている場合
        if pd.isna(row["zip"]):
            continue

        if int(row["zip"]) in not_on_zipcode_list:
            count_2 += 1
            # print(count_2)
            continue

        Path("weather_data").mkdir(exist_ok=True)
        save_folder = Path("weather_data__") / row["folder"]
        # 既にフォルダが作られている かつ フォルダの中身が3つとも入っている場合
        if save_folder.exists() and len(list(save_folder.iterdir())) == 3:
            count_2 += 1
            # print(count_2)
            continue

        # 被験者IDでフォルダを作成する.
        save_folder.mkdir(exist_ok=True, parents=True)

        pref_name = refer_jp_post(int(row["zip"]), postcode_list, pref_list)

        # 1時間毎の天気を取得して保存
        start_df, end_df = zip2weather(pref_name, row["sday"], row["eday"], mode='hourly', duration=1)
        start_df.to_csv(save_folder / "start.csv", index=False, encoding='shift_jis')
        end_df.to_csv(save_folder / "end.csv", index=False, encoding='shift_jis')

        # 一日毎の天気を取得
        daily_df = zip2weather(pref_name, row["sday"], row["eday"], mode='daily')
        daily_df.to_csv(save_folder / "daily.csv", index=False, encoding='shift_jis')
        aggregated_df = pd.concat([aggregated_df, daily_df], axis=0)

        if i % 100 == 0:
            print(f"{i} data finished")

    aggregated_df = pd.concat([source_df, aggregated_df.reset_index(drop=True)], axis=1)
    pass
