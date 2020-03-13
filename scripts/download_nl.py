import logging
import os
import io
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html
import lxml

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

class SARSCOV2NL(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="NL", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        doc = lxml.html.document_fromstring(self.req.text)
        el = doc.xpath('.//div[@id="csvData"]')
        if el:
            text = "".join(
                el[0].xpath('.//text()')
            )

        self.df = pd.read_csv(
            io.StringIO(text), sep=";", skiprows=[1,2,3], header=None
        )
        self.df = self.df[[0, 1, 2]]
        cols = text.split("\n")[1].split(";")
        self.df.columns = cols
        df_other = self.df.loc[self.df.Gemnr == -1]
        df_other.Gemeente = "Other"

        self.df = self.df.loc[
            self.df.Gemnr >= 0
        ]
        self.df = pd.concat([self.df, df_other])

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

        doc = lxml.html.document_fromstring(self.req.text)
        el = doc.xpath('.//div[@id="csvData"]')
        if el:
            text = "".join(
                el[0].xpath('.//text()')
            )

        re_dt = re.compile(r"peildatum (\d{1,2} \w+ \d{1,2}:\d{1,2})")
        dt_from_re = re_dt.findall(text)

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
    cov_nl = SARSCOV2NL()
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
