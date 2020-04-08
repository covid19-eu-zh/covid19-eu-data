import datetime
import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html
from utils import get_response as _get_response

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator, DailyTransformation, retrieve_files

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.wales")

# Wales Tableau
# https://public.tableau.com/profile/public.health.wales.health.protection#!/vizhome/RapidCOVID-19virology-Public/Headlinesummary
WALES_REPORT_URL_ALT = "https://covid19-phwstatement.nhs.wales/"
WALES_REPORT_URL = "https://phw.nhs.wales"
WALES_DAILY_FOLDER = os.path.join("dataset", "daily", "wales")


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
        try:
            req_dfs = pd.read_html(
                self.req.content, flavor='lxml'
            )
        except:
            self.req = _get_response(WALES_REPORT_URL_ALT)
            req_dfs = pd.read_html(
                self.req.content, flavor='lxml'
            )

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0]

        self.df.columns = ["nuts_3", "new_cases", "cases"]
        self.df = self.df[1:]
        self.df["nuts_3"] = self.df.nuts_3.apply(
            lambda x: x.replace("  ", " ").replace('*', '') if isinstance(x, str) else x
        )
        self.df["cases"] = self.df.cases.apply(
            lambda x: x.replace('*', '') if isinstance(x, str) else x
        )
        self.df["cases"] = self.df.cases.astype(int)
        logger.info("cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        # Last updated: 2pm on 16 March 2020
        re_dt = re.compile(r'Updated: (.*?)</i>')
        dt_from_re = re_dt.findall(self.req.text)
        re_hour = re.compile(r"This statement will be updated daily at (\d{1,2}\w+)")
        update_hour = re_hour.findall(self.req.text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0].replace('&nbsp;', ' ')
        dt_from_re = dateutil.parser.parse(dt_from_re)

        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)

        self.df.drop(
            self.df.loc[
                (
                    self.df['nuts_3'] == 'TOTAL'
                ) | (
                    self.df['nuts_3'] == 'Total'
                )
            ].index,
            inplace=True
        )

        self.df.replace("Wales Total", "", inplace=True)



if __name__ == "__main__":

    # column_converter = {
    #     "authority": "nuts_3"
    # }

    # daily_files = retrieve_files(WALES_DAILY_FOLDER)
    # daily_files.sort()

    # for file in daily_files:
    #     file_path = os.path.join(WALES_DAILY_FOLDER, file)
    #     file_transformation = DailyTransformation(
    #         file_path=file_path,
    #         column_converter=column_converter
    #     )
    #     file_transformation.workflow()

    cov_wales = SARSCOV2Wales()
    cov_wales.workflow()

    logger.info(cov_wales.df)

    da_wales = DailyAggregator(
        base_folder="dataset",
        daily_folder=WALES_DAILY_FOLDER,
        country="Wales"
    )
    da_wales.workflow()

    print("End of Game")
