import html
import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree
import lxml

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.at")

AT_REPORT_URL = "https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html"
DAILY_FOLDER = os.path.join("dataset", "daily", "at")
AT_STATES = [
    "Burgenland",
    "Kärnten",
    "Niederösterreich",
    "Oberösterreich",
    "Salzburg",
    "Steiermark",
    "Tirol",
    "Vorarlberg",
    "Wien"
]

class SARSCOV2AT(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = AT_REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="AT", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        re_cases = re.compile(r'\s(\w*?)\s\((\d+)\)')

        text = html.unescape(self.req.text)

        cases = [i for i in re_cases.findall(text) if i[0] in AT_STATES]

        if not cases:
            raise Exception("Could not find data table in webpage")

        self.df = pd.DataFrame(
            cases, columns=["state", "cases"]
        )

        self.df["cases"] = self.df.cases.astype(int)

        total = self.df.cases.sum()

        self.df = self.df.append(
            pd.DataFrame(
                [["sum", total]], columns=["state", "cases"]
            )
        )

        logger.info("de cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        Aktuelle Situation Österreich 04.03.2020 / 17:45 Uhr
        Stand, 10.03.2020, 08:00 Uhr
        """
        doc = lxml.html.document_fromstring(self.req.text)
        el = doc.xpath('.//div[@class="infobox"]')
        if el:
            text = "".join(
                el[0].xpath('.//text()')
            )

        re_dt = re.compile(r'Bestätigte Fälle, Stand (\d{1,2}.\d{1,2}.\d{4}, \d{1,2}:\d{1,2}) Uhr:')
        text = html.unescape(text)
        dt_from_re = re_dt.findall(text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0].replace("/", "")
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)


if __name__ == "__main__":
    cov_at = SARSCOV2AT()
    cov_at.workflow()

    print(cov_at.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="AT"
    )
    da.workflow()

    print("End of Game")
