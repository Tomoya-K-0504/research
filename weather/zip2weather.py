import sys
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd
import requests
from JmaScraper import JmaScraper
from bs4 import BeautifulSoup


def access_site(url):
    # スクレイピング先のサーバーに負荷がかかりすぎないよう、0.5秒おく
    time.sleep(0.5)
    html = requests.get(url).content
    soup = BeautifulSoup(html, "lxml")

    return html, soup


def zip_api(postal):
    """
    apiにアクセスして、郵便番号をキーにして県名を返す. 取得に失敗した場合はNaneを返す
    :param postal: 郵便番号
    :return: pref_name
    """
    url = "http://zip.cgis.biz/csv/zip.php?zn=" + str(postal).zfill(7)
    content = requests.get(url).text
    try:
        pref_name = content.split("\",\"")[12]
    except IndexError as e:
        print(e)
        print(postal)
        print(content.split("\",\""))
        return None
    return pref_name


def zip2pref(postal, postal_list, pref_list):
    """
    郵便局が提供しているcsvを使って、郵便番号と都道府県名を取得し、引数に該当する都道府県名を返す.
    csvに載っていない場合(事業所の郵便番号等)は、apiにアクセスして取得する.
    :param postal:
    res['postal'], res['prefecture'], res['city'], res['town'], res['y'], res['x']
    :return: 6570805, 兵庫県, 神戸市灘区, 青谷町一丁目, 34.712429, 135.214521
    """
    if postal in postal_list:
        index = postal_list.index(postal)
    else:
        print(f"postcode {postal} is not in jp_post postcode list.")
        return zip_api(postal)

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
        yesterday = sdate - timedelta(days=1)
        yesterday_df = JmaScraper(pref_name, year=yesterday.year, month=yesterday.month, day=yesterday.day).scrape()
        start_daily_df = JmaScraper(pref_name, year=sdate.year, month=sdate.month, day=sdate.day).scrape()
        end_daily_df = JmaScraper(pref_name, year=edate.year, month=edate.month, day=edate.day).scrape()

        # 該当する日付の行を抜き出し、カラム名を変更する
        yesterday_series = yesterday_df[yesterday_df["day"] == str(yesterday.day)][daily_columns]
        yesterday_series.columns = [f"p_{col}" for col in yesterday_series.columns]
        start_day_series = start_daily_df[start_daily_df["day"] == str(sdate.day)][daily_columns]
        start_day_series.columns = [f"s_{col}" for col in start_day_series.columns]
        end_day_series = end_daily_df[end_daily_df["day"] == str(edate.day)][daily_columns]
        end_day_series.columns = [f"e_{col}" for col in end_day_series.columns]

        # 連結して返す
        daily_series = pd.concat([
            yesterday_series.reset_index(drop=True),
            start_day_series.reset_index(drop=True),
            end_day_series.reset_index(drop=True)
        ], axis=1)
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

    # with open("not_on_zipcode_list.txt") as f:
    #     not_on_zipcode_list = f.read().split("\n")[:-1]
    # not_on_zipcode_list = [int(zipcode) for zipcode in not_on_zipcode_list]

    # 郵便局の郵便番号リストを読み込む
    df = pd.read_csv(Path(__file__).parent.resolve() / "KEN_ALL.CSV", encoding='shift-jis')
    postcode_list = list(set(df.iloc[:, 2].values))
    pref_list = df.iloc[:, 6].values

    count_2 = 0

    # 既にスクレイプしたファイルリストを読み込む
    # if Path("finished_list.txt").exists():
    #     with open(Path("finished_list.txt"), "r") as f:
    #         finished_list = f.read().split("\n")[:-1]

    Path("tmp").mkdir(exist_ok=True)

    # 郵便局のcsvにもapiにもないzipcodeの場合に使用する.
    pref_dict = {"7611400": "香川県", "791561": "北海道", "4280021": "静岡県", "5203243": "滋賀県", "5010801": "岐阜県",
                 "4618701": "愛知県"}

    # 各データごとに、開始日の天気と終了日の天気をスクレイピングする
    for i, row in source_df.iterrows():

        # 既にスクレイプしたファイルリストに含まれていればスキップ
        # if row["folder"] in finished_list:
        #     continue

        # 元データに郵便番号がはいっていない場合
        if pd.isna(row["zip"]):
            with open("failure_list.txt", "a") as f:
                f.write(str(row["folder"]) + "," + str(row["zip"]) + "\n")
            continue

        # 郵便局のデータに載っていないリストに郵便番号が入っている場合
        # if int(row["zip"]) not in not_on_zipcode_list:
        #     count_2 += 1
            # print(count_2)
            # continue

        save_folder = Path("tmp") / row["folder"]
        # 既にフォルダが作られている かつ フォルダの中身が3つとも入っている場合
        if save_folder.exists() and len(list(save_folder.iterdir())) == 3:
            count_2 += 1
            # print(count_2)
            continue

        # 被験者IDでフォルダを作成する.
        save_folder.mkdir(exist_ok=True, parents=True)

        pref_name = zip2pref(int(row["zip"]), postcode_list, pref_list)

        # apiを使ってもpref_nameの取得に失敗した場合、pref_dictにある県名を取得する.
        if not pref_name:
            pref_name = pref_dict[str(int(row["zip"]))]

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
