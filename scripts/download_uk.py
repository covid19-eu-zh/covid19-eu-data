import datetime
import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.uk")

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
                "GSS_NM": "authority",
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

        self.df.rename(columns={
            "Health board": "authority",
            "Positive cases": "cases"
        }, inplace=True)
        logger.info("cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        # Last updated: 2pm on 16 March 2020
        re_dt = re.compile(r'ast updated: (\d{1,2}pm on \d{1,2} \w+ \d{4})\.')
        dt_from_re = re_dt.findall(self.req.text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)



class SARSCOV2Wales(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = WALES_REPORT_URL

        if daily_folder is None:
            daily_folder = WALES_DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="Wales", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """
        req_dfs = pd.read_html(
            self.req.content, flavor='lxml'
        )

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0]

        self.df.columns = ["authority", "previous_day_cases", "new_cases", "cases"]
        self.df = self.df[1:]
        logger.info("cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        # Last updated: 2pm on 16 March 2020
        re_dt = re.compile(r'Updated: (.*)&nbsp;(.*)&nbsp;(.*)</em></p>')
        dt_from_re = re_dt.findall(self.req.text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        dt_from_re = " ".join(dt_from_re)
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)



if __name__ == "__main__":

    cov_wales = SARSCOV2Wales()
    cov_wales.workflow()

    da_wales = DailyAggregator(
        base_folder="dataset",
        daily_folder=WALES_DAILY_FOLDER,
        country="Wales"
    )
    da_wales.workflow()


    cov_england = SARSCOV2England()
    cov_england.workflow()

    da_england = DailyAggregator(
        base_folder="dataset",
        daily_folder=ENGLAND_DAILY_FOLDER,
        country="England"
    )
    da_england.workflow()

    cov_scotland = SARSCOV2Scotland()
    cov_scotland.workflow()

    da_scotland = DailyAggregator(
        base_folder="dataset",
        daily_folder=SCOTLAND_DAILY_FOLDER,
        country="Scotland"
    )
    da_scotland.workflow()



    print("End of Game")
