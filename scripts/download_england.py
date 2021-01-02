import datetime
import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.england")

# https://www.arcgis.com/home/item.html?id=b684319181f94875a6879bbc833ca3a6
# REPORT_URL = "https://www.gov.uk/government/publications/coronavirus-covid-19-number-of-cases-in-england/coronavirus-covid-19-number-of-cases-in-england"
ENGLAND_REPORT_URL = "https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data"
ENGLAND_DAILY_FOLDER = os.path.join("dataset", "daily", "england")
SCOTLAND_REPORT_URL = "https://www.gov.scot/coronavirus-covid-19/"
SCOTLAND_DAILY_FOLDER = os.path.join("dataset", "daily", "scotland")
WALES_REPORT_URL = "https://phw.nhs.wales/news/public-health-wales-statement-on-novel-coronavirus-outbreak/"
WALES_DAILY_FOLDER = os.path.join("dataset", "daily", "wales")

class SARSCOV2England(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = ENGLAND_REPORT_URL

        if daily_folder is None:
            daily_folder = ENGLAND_DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="England", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """
        req_dfs = pd.read_csv(ENGLAND_REPORT_URL)

        if req_dfs.empty:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs
        self.df.rename(
            columns = {
                "GSS_NM": "nuts_3",
                "TotalCases": "cases"
            },
            inplace=True
        )

        logger.info("records of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        current_date = datetime.datetime.now()
        self.dt = datetime.datetime(
            current_date.year, current_date.month, current_date.day
        )

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)

    def cache(self):

        self.df = self.df[
            [i for i in _COLUMNS_ORDER if i in self.df.columns]
        ]
        exists = False
        for d in os.listdir(f"{self.daily_folder}"):
            df_existing = pd.read_csv(
                os.path.join(self.daily_folder, d)
            )
            if self.df.equals(df_existing):
                exists = True
                logger.info("Current data frame already exists")
                break

        if not exists:
            self.df.to_csv(
                f"{self.daily_folder}/{self.country.lower()}_covid19_{self.date}_{self.hour:0.0f}_{self.minute:02.0f}.csv",
                index=False
            )



if __name__ == "__main__":

    # column_converter = {
    #     "authority": "nuts_3"
    # }

    # daily_files = retrieve_files(ENGLAND_DAILY_FOLDER)
    # daily_files.sort()

    # for file in daily_files:
    #     file_path = os.path.join(ENGLAND_DAILY_FOLDER, file)
    #     file_transformation = DailyTransformation(
    #         file_path=file_path,
    #         column_converter=column_converter
    #     )
    #     file_transformation.workflow()

    cov_england = SARSCOV2England()
    cov_england.workflow()

    da_england = DailyAggregator(
        base_folder="dataset",
        daily_folder=ENGLAND_DAILY_FOLDER,
        country="England"
    )
    da_england.workflow()




    print("End of Game")
