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
logger = logging.getLogger("covid-eu-data.download.scotland")

# https://www.arcgis.com/home/item.html?id=b684319181f94875a6879bbc833ca3a6
# REPORT_URL = "https://www.gov.uk/government/publications/coronavirus-covid-19-number-of-cases-in-england/coronavirus-covid-19-number-of-cases-in-england"

# SCOTLAND_REPORT_URL = "https://www.gov.scot/coronavirus-covid-19/"
SCOTLAND_REPORT_URL = "https://www.gov.scot/publications/coronavirus-covid-19-tests-and-cases-in-scotland/"
SCOTLAND_DAILY_FOLDER = os.path.join("dataset", "daily", "scotland")


class SARSCOV2Scotland(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = SCOTLAND_REPORT_URL

        if daily_folder is None:
            daily_folder = SCOTLAND_DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="Scotland", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """
        req_dfs = pd.read_html(
            self.req.content, flavor='lxml'
        )

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0]
        if 'Health board' not in self.df.columns:
            self.df.columns = self.df.iloc[0]
            self.df = self.df.loc[1:,:]

        self.df.rename(columns={
            "Health board": "nuts_3",
            "Positive cases": "cases",
            "Positive Cases": "cases",
            "Total confirmed cases to date": "cases",
            "People in hospital at midnight (confirmed or suspected)": "hospitalized",
            "People in intensive care at midnight (confirmed or suspected)": "intensive_care"
        }, inplace=True)
        self.df.replace("*", "", inplace=True)
        logger.info("cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        # Last updated: 2pm on 16 March 2020
        # Scottish COVID-19 test numbers: 2 May 2020
        # Published: 2 May 2020
        re_dt = re.compile(r'Scottish numbers: (.*?)</')
        dt_from_re = re_dt.findall(self.req.text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0].replace("&nbsp;", " ")
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)


if __name__ == "__main__":

    # column_converter = {
    #     "nuts_2": "nuts_3"
    # }

    # daily_files = retrieve_files(SCOTLAND_DAILY_FOLDER)
    # daily_files.sort()

    # for file in daily_files:
    #     file_path = os.path.join(SCOTLAND_DAILY_FOLDER, file)
    #     file_transformation = DailyTransformation(
    #         file_path=file_path,
    #         column_converter=column_converter
    #     )
    #     file_transformation.workflow()

    cov_scotland = SARSCOV2Scotland()
    cov_scotland.workflow()

    da_scotland = DailyAggregator(
        base_folder="dataset",
        daily_folder=SCOTLAND_DAILY_FOLDER,
        country="Scotland"
    )
    da_scotland.workflow()



    print("End of Game")
