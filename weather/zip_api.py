import json

import requests


def zip2geo_api3(postal):
    """
    urlのサイトのAPIを使用. 事業所の郵便番号は登録されていない.
    :param postal: 郵便番号 (ハイフン有は可)
    :return: 県名
    """
    url = "http://geoapi.heartrails.com/api/xml?method=searchByPostal&postal="

    content = json.loads(requests.get(f"{url}{str(postal).zfill(7)}").text)
    return content["results"][0]["address1"]


def zip2geo_api2(postal):
    """
    urlのサイトのAPIを使用. 事業所の郵便番号は登録されていない.
    :param postal: 郵便番号 (ハイフン有は可)
    :return: 県名
    """
    url = "http://zipcloud.ibsnet.co.jp/api/search?zipcode="
    _ = f"{url}{str(postal).zfill(7)}"
    content = json.loads(requests.get(f"{url}{str(postal).zfill(7)}").text)
    return content["results"][0]["address1"]


def zip2geo_api1(postal):
    """
    このサイト→http://zip.cgis.biz/ のAPIを利用. 利用回数制限あり.
    :param postal: 郵便番号 (ハイフン有は不可)
    :return: 県名
    """

    # 以下は一旦使用しない。多くアクセスすると切られるので。
    url = 'http://zip.cgis.biz/csv/zip.php?zn='

    # 北海道などは0から郵便番号が始まり、おそらくexcelの仕様的に初めの0を消してしまうので、7桁になるよう0を先頭から埋める
    content = requests.get(f"{url}{str(postal).zfill(7)}").text
    # decodeした結果がstr型で、xmlでパースがなぜかできなかったので、改行でsplitして県名が入った部分を取り出し、県名のみ切り出す
    pref_name = content.split("\",\"")[12]

    return pref_name
