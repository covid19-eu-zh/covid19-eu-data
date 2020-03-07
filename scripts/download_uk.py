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

REPORT_URL = "https://www.gov.uk/government/publications/coronavirus-covid-19-number-of-cases-in-england/coronavirus-covid-19-number-of-cases-in-england"
DAILY_FOLDER = os.path.join("dataset", "daily", "uk")

def parse_cases(cases):
    """
    parse_cases parse the uk record and returns the lower and upper limits of the cases.

    UK use ranges in their reports. For example, they use 1 to 4 as a range indicator.
    """
    res_lower = None
    res_upper = None

    try:
        res = int(float(cases))
        res_lower = res
        res_upper = res
    except ValueError as ve:
        re_cases = re.compile(r"(\d) to (\d)")
        res = re_cases.findall(cases)
        if res:
            res_lower = res[0][0]
            res_upper = res[0][1]
        else:
            logger.error(f"Could extract lower and upper bounds from {cases}")

    return (res_lower, res_upper)


class SARSCOV2DE(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="UK", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """
        req_dfs = pd.read_html(self.req.content, flavor='lxml')

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0][["Local authority","Number of confirmed cases"]]
        self.df.rename(
            columns = {
                "Local authority": "authority",
                "Number of confirmed cases": "cases"
            },
            inplace=True
        )
        self.df["cases_lower"] = self.df["cases"].apply(lambda x: parse_cases(x)[0])
        self.df["cases_upper"] = self.df["cases"].apply(lambda x: parse_cases(x)[1])

        logger.info("records of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        re_dt = re.compile(r"These data are as of (.+?)\.")
        dt_from_re = re_dt.findall(self.req.text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        dt_from_re = dateutil.parser.parse(dt_from_re)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)
        self.df.replace("Gesamt", "sum", inplace=True)


if __name__ == "__main__":
    cov_uk = SARSCOV2DE()
    cov_uk.workflow()

    print(cov_uk.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="UK"
    )
    da.workflow()

    print("End of Game")
