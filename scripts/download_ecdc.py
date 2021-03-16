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
logger = logging.getLogger("covid-eu-data.download.scotland")

REPORT_URL = "https://www.ecdc.europa.eu/en/cases-2019-ncov-eueea"
DAILY_FOLDER = os.path.join("dataset", "daily", "ecdc")

EU_ALPHA2 = {'Italy': 'IT',
 'Spain': 'ES',
 'France': 'FR',
 'Germany': 'DE',
 'United Kingdom': 'GB',
 'United_Kingdom': 'GB',
 'Netherlands': 'NL',
 'Austria': 'AT',
 'Belgium': 'BE',
 'Norway': 'NO',
 'Sweden': 'SE',
 'Denmark': 'DK',
 'Portugal': 'PT',
 'Czech Republic': 'CZ',
 'Czech_Republic': 'CZ',
 'Czechia': 'CZ',
 'Greece': 'GR',
 'Finland': 'FI',
 'Ireland': 'IE',
 'Poland': 'PL',
 'Slovenia': 'SI',
 'Romania': 'RO',
 'Estonia': 'EE',
 'Iceland': 'IS',
 'Luxembourg': 'LU',
 'Slovakia': 'SK',
 'Bulgaria': 'BG',
 'Croatia': 'HR',
 'Hungary': 'HU',
 'Latvia': 'LV',
 'Cyprus': 'CY',
 'Malta': 'MT',
 'Lithuania': 'LT',
 'Liechtenstein': 'LI',
 'Total': 'Total'}

class SARSCOV2ECDC(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="ECDC", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """
        req_dfs = pd.read_html(REPORT_URL)

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0]

        if (
            "Sum of Cases" not in self.df.columns
        ) and (
            "Cases" not in self.df.columns
        ):
            new_header = self.df.iloc[0] #grab the first row for the header
            self.df = self.df[1:] #take the data less the header row
            self.df.columns = new_header

        self.df.rename(
            columns = {
                "EU/EEA and the UK": "country",
                "EU/EEA": "country",
                "Country": "country",
                "Cases": "cases",
                "Sum of Cases": "cases",
                "Deaths": "deaths",
                "Sum of Deaths": "deaths",
                "14-day case notification rate per 100 000 inhabitants for the reporting period": "cases/100k pop.",
                "14-day death notification rate per 100 000 inhabitants  for the reporting period": "deaths/100k pop."
            },
            inplace=True
        )

        self.df["country"] = self.df.country.apply(
            lambda x: EU_ALPHA2[x]
        )

        # self.df.replace("Total", "sum", inplace=True)
        for col in self.df.columns:
            try:
                self.df[col] = self.df[col].str.replace(" ", "")
            except:
                pass

        logger.info("records of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """

        doc = html.document_fromstring(self.req.content.decode("utf-8"))
        el = doc.xpath('.//div[@class="ct__page-content"]')
        if el:
            text = el[0].xpath('.//h1/span/text()')[0]

        # re_dt = re.compile(r'as of (.*)')
        re_dt = re.compile(r'as of .* (\d+\s\w+\s\d+)')
        re_dt_res = re_dt.findall(el[0].xpath('.//h1/span/text()')[0])
        if not re_dt_res:
            raise Exception("Could not find datetime on the web page")

        # self.dt = dateutil.parser.parse(re_dt_res[0], dayfirst=True)
        # self.dt = datetime.datetime.strptime(re_dt_res[0] + " 1", "week %W %Y %w")
        self.dt = pd.to_datetime(re_dt_res[0])

    def add_country_to_df(self):

        logger.debug("No need to add country")

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)


if __name__ == "__main__":


    cov_ecdc = SARSCOV2ECDC()
    cov_ecdc.workflow()

    da_ecdc = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="ECDC"
    )
    da_ecdc.workflow()



    print("End of Game")
