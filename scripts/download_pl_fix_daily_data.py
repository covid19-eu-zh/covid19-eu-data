import datetime
import json
import logging
import os
import re
import io
import zipfile

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files, get_response)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.pl.fix_daily")

# REPORT_URL = "https://www.gov.pl/web/koronawirus/wykaz-zarazen-koronawirusem-sars-cov-2"

REPORT_URL = "https://covid19-rcb-info.hub.arcgis.com/"
DATA_DATE_URL = "https://services9.arcgis.com/RykcEgwHWuMsJXPj/arcgis/rest/services/global_corona_actual_widok2/FeatureServer/0/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&resultOffset=0&resultRecordCount=1&resultType=standard&cacheHint=true"
# CSV_DATA_URL = "https://arcgis.com/sharing/rest/content/items/829ec9ff36bc45a88e1245a82fff4ee0/data"
CSV_DATA_URL = "https://arcgis.com/sharing/rest/content/items/153a138859bb4c418156642b5b74925b/data"
MONTHLY_ARCHIVE_URL = "https://arcgis.com/sharing/rest/content/items/a8c562ead9c54e13a135b02e0d875ffb/data"
DAILY_FOLDER = os.path.join("dataset", "daily", "pl")


def download_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)


map_nuts_2 = {
    '\x9cl¹skie': 'śląskie',
    'zachodniopomorskie': 'zachodniopomorskie',
    'pomorskie': 'pomorskie',
    'kujawsko-pomorskie': 'kujawsko-pomorskie',
    'wielkopolskie': 'wielkopolskie',
    '\x9cwiêtokrzyskie': 'świętokrzyskie',
    'mazowieckie': 'mazowieckie',
    'opolskie': 'opolskie',
    'podkarpackie': 'podkarpackie',
    'podlaskie': 'podlaskie',
    'lubuskie': 'lubuskie',
    'ma³opolskie': 'małopolskie',
    'lubelskie': 'lubelskie',
    'dolno\x9cl¹skie': 'dolnośląskie',
    'warmiñsko-mazurskie': 'warmińsko-mazurskie',
    '³ódzkie': 'łódzkie'
}

if __name__ == "__main__":

    DAILY_FOLDER = os.path.join("dataset", "daily", "pl")

    file_list = sorted(os.listdir(DAILY_FOLDER))
    df_previous = pd.read_csv(os.path.join(DAILY_FOLDER, file_list[0]))
    check_loc = "lubuskie"
    problem_date_start = pd.to_datetime("2020-11-24")
    for f in file_list[1:]:
        f_path = os.path.join(DAILY_FOLDER, f)
        df_f = pd.read_csv(f_path)
        f_dt = pd.to_datetime(df_f["datetime"]).max()
        cols = ["cases"]
        if "deaths" in df_f.columns:
            cols.append("deaths")
        if f_dt >= problem_date_start:
            check_loc_value = df_f.loc[df_f.nuts_2 == check_loc]["cases"].max()
            prev_check_loc_value = df_previous.loc[
                df_previous.nuts_2 == check_loc
            ]["cases"].max()
            df_f.replace(map_nuts_2, inplace=True)
            if prev_check_loc_value >= check_loc_value:
                # calculate culumative values
                df_f = df_f.replace(map_nuts_2).merge(
                    df_previous[["nuts_2"] + cols],
                    how="left",
                    on="nuts_2",
                    suffixes=["", "_prev"]
                )
                for col in cols:
                    df_f[col] = df_f[col].fillna(0).astype(int) + df_f[f"{col}_prev"].fillna(0).astype(int)

                df_f.drop([f"{c}_prev" for c in cols], axis=1, inplace=True)
                df_f.to_csv(f_path, index=False)
        df_previous = df_f.copy()

    print("End of Game")
