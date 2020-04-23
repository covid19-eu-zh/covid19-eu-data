import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files, get_response)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.si")

XLSX_DATA_URL = "https://www.gov.si/assets/vlada/Koronavirus-podatki/en/EN_Covid-19-all-data.xlsx"
REPORT_URL = "https://www.gov.si/en/topics/coronavirus-disease-covid-19/"
DAILY_FOLDER = os.path.join("dataset", "daily", "si")
CACHE_FOLDER = os.path.join("cache", "daily", "si")

class SARSCOV2SI(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="SI", daily_folder=daily_folder)

    def _extract_table_from_webpage(self):
        """Load data table from web page
        """
        req_dfs = pd.read_html(self.req.content, flavor='lxml')

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0]

        self.df.rename(
            columns={
                "Date": "datetime",
                "Tested": "tests",
                "Positive": "cases",
                "Hospitalized": "hospitalized",
                "Intensive care": "intensive_care",
                "Death": "deaths"
            }, inplace=True
        )
        self.df["datetime"] = self.df.datetime.apply(
            lambda x: dateutil.parser.parse(x, dayfirst=True).isoformat()
        )

        self.dt = dateutil.parser.parse(self.df.datetime.values.max())

        logger.info("records cases:\n", self.df)

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)


def cache_table():
    req_dfs = pd.read_html(REPORT_URL, flavor='lxml')

    if not req_dfs:
        raise Exception("Could not find data table in webpage")

    df = req_dfs[0]

    dt = dateutil.parser.parse(df.iloc[0].Date, dayfirst=True)

    logger.info("records cases:\n", df)

    df.to_csv(
        f"{CACHE_FOLDER}/{dt.isoformat()}.csv",
        index=False
    )

    with open(
            os.path.join(CACHE_FOLDER, f"{dt.isoformat()}.html"),
            'wb'
        ) as f:
            f.write(get_response(REPORT_URL).content)


def download_and_xlsx(xlsx_url):


    with open(
            os.path.join(CACHE_FOLDER, f"full_data.xlsx"),
            'wb'
        ) as f:
            f.write(get_response(xlsx_url).content)

    df = pd.read_excel(xlsx_url)

    cols = {
        "Date": "datetime",
        "Tested (all)": "tests",
        "Positive (all)": "tests_positive",
        "All hospitalized on certain day": "hospitalized",
        "All persons in intensive care on certain day": "intensive_care",
        "Deaths (all)": "deaths"
    }

    df = df[list(cols.keys())]
    df.rename(columns=cols, inplace=True)
    df["cases"] = df.tests_positive
    df["country"] = "SI"
    df = df[[i for i in _COLUMNS_ORDER if i in df.columns]]
    df["datetime"] = df.datetime.apply(
        lambda x: x.isoformat()
    )
    df.sort_values(by=["datetime", "cases"], inplace=True)

    full_csv = os.path.join("dataset", "covid-19-si.csv")
    df.to_csv(
        full_csv, index=False
    )


if __name__ == "__main__":

    download_and_xlsx(XLSX_DATA_URL)

    cache_table()

    print("End of Game")
