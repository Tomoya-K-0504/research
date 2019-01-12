import json
import sys
import re
import urllib
from pathlib import Path

import pandas as pd
import requests


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


def get_weather_info(postcode: str):
    # 郵便局の郵便番号リストを読み込む
    df = pd.read_csv(Path(__file__).parent.parent.resolve() / "data" / "KEN_ALL.CSV", encoding='shift-jis')
    postcode_list = list(set(df.iloc[:, 2].values))
    pref_list = df.iloc[:, 6].values

    # 郵便局のcsvにもapiにもないzipcodeの場合に使用する.
    pref_dict = {"7611400": "香川県", "791561": "北海道", "4280021": "静岡県", "5203243": "滋賀県", "5010801": "岐阜県",
                 "4618701": "愛知県"}

    pref_name = zip2pref(postcode, postcode_list, pref_list)

    # apiを使ってもpref_nameの取得に失敗した場合、pref_dictにある県名を取得する.
    if not pref_name:
        try:
            pref_name = pref_dict[str(postcode)]
        except KeyError as e:
            print(e)
            print("couldn't get Prefecture name from {}".format(postcode))

    # 北海道の場合は道央にする. あとで札幌になる
    if pref_name == "北海道":
        pref_name = "道央"

    with open(Path(__file__).parent.parent.resolve() / "data" / "primary_area.xml") as f:
        data = f.read()
    pref_list = data.split("pref title=\"")[1:]
    pref_id_converter = {}
    for pref_str in pref_list:
        pref_id_converter[pref_str[:4].replace("\"", "").replace(">", "")] = re.search("id=\"(\d+)\"", pref_str).group(1)

    WEATHER_URL = "http://weather.livedoor.com/forecast/webservice/json/v1?city=%s"
    CITY_CODE = pref_id_converter[pref_name]

    try:
        url = WEATHER_URL % CITY_CODE
        html = urllib.request.urlopen(url)
        html_json = json.loads(html.read().decode('utf-8'))
    except Exception as e:
        print ("Exception Error: ", e)
        sys.exit(1)
    return html_json["forecasts"][0]["telop"]


if __name__ == "__main__":
    data = get_weather_info()
    print(data)
