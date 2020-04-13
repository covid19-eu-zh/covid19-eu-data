import io
import logging
import os
import re

import dateutil
import lxml
import pandas as pd
import requests
from lxml import etree, html

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.hu")

REPORT_URL = "https://koronavirus.gov.hu/"
DAILY_FOLDER = os.path.join("dataset", "daily", "hu")

class SARSCOV2HU(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="HU", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        doc = lxml.html.document_fromstring(self.req.text)
        el_numbers = doc.xpath('.//div[@class="diagram-a"]/span[@class="number"]/text()')
        el_labels = doc.xpath('.//div[@class="diagram-a"]/span[@class="label"]/text()')
        if el_numbers:
            data = dict(zip(el_labels, el_numbers))

        self.df = pd.DataFrame(
            [data]
        )

        self.df.rename(
            columns = {
                "Fertőzött": "cases",
                "Gyógyult": "recovered",
                "Elhunyt": "deaths",
                "Karanténban": "quarantine",
                "Mintavétel": "tests"
            }, inplace=True
        )

        for col in ["cases", "recovered", "deaths", "tests", "quarantine"]:
            try:
                self.df[col] = self.df[col].apply(
                    lambda x: int(
                        float(
                            x.replace(" ", "")
                        )
                    )
                )
            except KeyError as ke:
                logger.error(f'Could not find column {col}')
                self.df[col] = ''

        logger.info("list of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """

        # Legutolsó frissítés dátuma: 2020.03.24. 11:15
        doc = lxml.html.document_fromstring(self.req.text)
        el = doc.xpath('.//div[contains(@class, "view-diagrams")]')
        if el:
            text = "".join(
                el[0].xpath('.//text()')
            )
        # <p>Legutolsó frissítés dátuma: 2020.03.24. 11:15 </p>
        re_dt = re.compile(r"Legutolsó frissítés dátuma: (.*?)\n")
        dt_from_re = re_dt.findall(text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        dt_from_re = dateutil.parser.parse(dt_from_re)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)


if __name__ == "__main__":

    cov_hu = SARSCOV2HU()
    cov_hu.workflow()

    print(cov_hu.df)
    if cov_hu.df.empty:
        raise Exception("Empty dataframe")

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="HU"
    )
    da.workflow()

    print("End of Game")
