import urllib
import json
import sys
from jitai.config import const


def get_weather_info(city="神戸"):

    with open(const.PJ_ROOT / "primary_area.xml") as f:
        data = f.read()
    id_list = data.split("city title=\"")[1:]
    _ = {_id[0:4]: _id[8:16] for _id in id_list}

    id_dict = {}
    for key, value in _.items():
        id_dict[key.replace("\"", "").replace(" ", "")] = value.replace("\"", "").replace(" ", "").replace("=", "")

    WEATHER_URL = "http://weather.livedoor.com/forecast/webservice/json/v1?city=%s"
    CITY_CODE = id_dict[city]

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
