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
logger = logging.getLogger("covid-eu-data.download.si")

REPORT_URL = "https://www.gov.si/en/topics/coronavirus-disease-covid-19/"
DAILY_FOLDER = os.path.join("dataset", "daily", "si")

class SARSCOV2SI(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="SI", daily_folder=daily_folder)

    def extract_table(self):
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



if __name__ == "__main__":

    cov_si = SARSCOV2SI()
    cov_si.workflow()

    print(cov_si.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="si"
    )
    da.workflow()

    print("End of Game")
