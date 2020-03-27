import html
import logging
import os
import re
from functools import reduce
import json

import dateutil
import lxml
import pandas as pd
import requests
from lxml import etree

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files, get_response)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.at")

AT_BUNDESLAND_URL = "https://info.gesundheitsministerium.at/data/Bundesland.js"
AT_TOTAL_URL = "https://info.gesundheitsministerium.at/data/SimpleData.js"
AT_REPORT_URL = "https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html"

HOSPITALIZED = "https://www.sozialministerium.at/Informationen-zum-Coronavirus/Dashboard/Zahlen-zur-Hospitalisierung"
DAILY_FOLDER = os.path.join("dataset", "daily", "at")
CACHE_FOLDER = os.path.join("cache", "daily", "at")
AT_STATES = {
    "Bgld": "Burgenland",
    "Ktn": "Kärnten",
    "NÖ": "Niederösterreich",
    "OÖ": "Oberösterreich",
    "Sbg": "Salzburg",
    "Stmk": "Steiermark",
    "T": "Tirol",
    "Vbg": "Vorarlberg",
    "W": "Wien"
}

class SARSCOV2AT(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = AT_REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="AT", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        geo_loc_key = 'nuts_2'

        hos_df = pd.read_html(HOSPITALIZED)
        if not hos_df:
            raise Exception("Could not find hospitalized table")
        hos_df = hos_df[0]
        hos_df.rename(
            columns = {
                "Bundesland": geo_loc_key,
                "Hospitalisierung": "hospitalized",
                "Intensivstation": "intensive_care"
            },
            inplace=True
        )
        hos_df.replace("Österreich gesamt", "", inplace=True)
        hos_df["hospitalized"] = hos_df.hospitalized.astype(int)
        hos_df["intensive_care"] = hos_df.intensive_care.astype(int)

        cases_req = get_response(AT_BUNDESLAND_URL)
        re_cases = re.compile(r'var dpBundesland = (\[.*\]);')
        cases = re_cases.findall(cases_req.text)[0]
        cases = json.loads(cases)
        cases = [
            {geo_loc_key: AT_STATES[i["label"]], "cases": int(i["y"])}
            for i in cases
        ]
        cases_total_req = get_response(AT_TOTAL_URL)
        re_cases_total = re.compile(r'var Erkrankungen = (\d+);')
        cases_total = re_cases_total.findall(cases_total_req.text)[0]
        cases_total = {geo_loc_key: "", "cases": cases_total}
        cases.append(cases_total)
        df_cases = pd.DataFrame(cases)

        self.df = pd.merge(
            df_cases, hos_df, how="outer",
            on=geo_loc_key
        )
        self.df.fillna("", inplace=True)
        self.df["cases"] = self.df.cases.astype(int)
        # self.df["hospitalized"] = self.df.hospitalized.astype(int)
        # self.df["intensive_case"] = self.df.intensive_case.astype(int)

        logger.info("cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        Aktuelle Situation Österreich 04.03.2020 / 17:45 Uhr
        Stand, 10.03.2020, 08:00 Uhr
        Stand 27.03.2020, 08:00 Uhr
        """
        req = get_response(HOSPITALIZED)

        re_dt = re.compile(r'Stand (\d+.\d+.\d+, \d+:\d+) Uhr')
        text = html.unescape(req.content.decode(req.apparent_encoding))
        dt_from_re = re_dt.findall(text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0].replace("/", "")
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)


def cache_content(url, dt, name):
    req = get_response(url)
    with open(
            os.path.join(CACHE_FOLDER, f"{dt}__{name}"),
            'wb'
        ) as f:
            f.write(req.content)

if __name__ == "__main__":

    # column_converter = {
    #     "state": "nuts_2"
    # }
    # drop_rows = {
    #     "state": "sum"
    # }

    # daily_files = retrieve_files(DAILY_FOLDER)
    # daily_files.sort()

    # for file in daily_files:
    #     file_path = os.path.join(DAILY_FOLDER, file)
    #     file_transformation = DailyTransformation(
    #         file_path=file_path,
    #         column_converter=column_converter,
    #         drop_rows=drop_rows
    #     )
    #     file_transformation.workflow()

    cov_at = SARSCOV2AT()
    cov_at.workflow()

    print(cov_at.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="AT",
        fill=False
    )
    da.workflow()

    to_be_cached ={
        "Bezirke.js": "https://info.gesundheitsministerium.at/data/Bezirke.js",
        "Geschlechtsverteilung.js": "https://info.gesundheitsministerium.at/data/Geschlechtsverteilung.js",
        "Altersverteilung.js": "https://info.gesundheitsministerium.at/data/Altersverteilung.js",
        "SimpleData.js": "https://info.gesundheitsministerium.at/data/SimpleData.js",
        "Coronavirus.html": "https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html"
    }
    for key,val in to_be_cached.items():
        cache_content(val, cov_at.datetime, key)

    print("End of Game")
