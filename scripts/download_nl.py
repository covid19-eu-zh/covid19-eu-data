import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.nl")

REPORT_URL = "https://www.volksgezondheidenzorg.info/onderwerp/infectieziekten/regionaal-internationaal/coronavirus-covid-19#node-coronavirus-covid-19-meldingen"
REPORT_CSV_BASE_URL = "https://www.volksgezondheidenzorg.info"
DAILY_FOLDER = os.path.join("dataset", "daily", "nl")
DUTCH_MONTHS_TO_EN = {
    'januari': 'january',
    'februari': 'february',
    'maart': 'march',
    'april': 'april',
    'mei': 'may',
    'juni': 'june',
    'juli': 'july',
    'augustus': 'august',
    'september': 'september',
    'oktober': 'october',
    'november': 'november',
    'december': 'december'
}

class SARSCOV2DE(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="NL", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """
        re_csv_url = re.compile(r'/sites/.+.csv')

        csv_urls = re_csv_url.findall(self.req.text)

        if csv_urls:
            csv_data_url = REPORT_CSV_BASE_URL + csv_urls[0]
            logger.info(f"csv file url: {csv_data_url}")
        else:
            raise Exception("Did not find csv file on page!")

        self.df = pd.read_csv(csv_data_url, sep=";")
        # Only take the numbers
        self.df = self.df.loc[
            (
                self.df.Indicator == "Aantal"
            ) | (
                self.df.Indicator == "Aantal gevallen"
            )
        ]
        self.df = self.df[["Gemeente", "Aantal"]]
        self.df.fillna(0, inplace=True)
        self.df["Aantal"] = self.df.Aantal.astype(int)
        # add sum
        total = self.df.Aantal.sum()
        self.df = self.df.append(
            pd.DataFrame(
                [["sum", total]], columns=["Gemeente", "Aantal"]
            )
        )

        logger.info("list of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        re_dt = re.compile(r"Per gemeente \(waar de patiënt woont\), peildatum (\d{1,2} \w+ \d{4})")
        dt_from_re = re_dt.findall(self.req.text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        for key in DUTCH_MONTHS_TO_EN:
            if key in dt_from_re:
                dt_from_re = dt_from_re.replace(key, DUTCH_MONTHS_TO_EN[key])
                break
        dt_from_re = dateutil.parser.parse(dt_from_re)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.rename(
            columns={
                "Gemeente": "city",
                "Aantal": "cases"
            },
            inplace=True
        )

        self.df = self.df[["country", "city", "cases", "datetime"]]

        self.df.sort_values(by="cases", inplace=True)


if __name__ == "__main__":
    cov_nl = SARSCOV2DE()
    cov_nl.workflow()

    print(cov_nl.df)
    if cov_nl.df.empty:
        raise Exception("Empty dataframe for NL data")

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="NL"
    )
    da.workflow()

    print("End of Game")
