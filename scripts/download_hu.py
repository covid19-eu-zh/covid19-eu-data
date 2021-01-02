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
        numbers_div = doc.xpath('.//div[@id="numbers-API"]/div')
        data = {i.xpath("./@id")[0]: i.xpath("./text()")[0].strip().replace(" ", "") for i in numbers_div}
        # <div id="numbers-API" class="alittleHelpForYourAPI hidden">
        #     <div id="api-fertozott-pest">1 290</div>
        #     <div id="api-fertozott-videk">764</div>
        #     <div id="api-gyogyult-pest">319</div>
        #     <div id="api-gyogyult-videk">311</div>
        #     <div id="api-elhunyt-pest">276</div>
        #     <div id="api-elhunyt-videk">75</div>
        #     <div id="api-karantenban">10 459</div>
        #     <div id="api-mintavetel">83 958</div>
        #     <div id="api-elhunyt-global">248 097</div>
        #     <div id="api-fertozott-global">3 529 408</div>
        #     <div id="api-gyogyult-global">1 133 538</div>
        # </div>
        self.df = pd.DataFrame([data])

        if self.df.empty:
            raise Exception("No data found")

        self.df.rename(
            columns = {
                "api-fertozott-pest": "cases_pest",
                "api-fertozott-videk": "cases_countryside",
                "api-gyogyult-pest": "recovered_pest",
                "api-gyogyult-videk": "recovered_countryside",
                "api-elhunyt-pest": "deaths_pest",
                "api-elhunyt-videk": "deaths_countryside",
                "api-karantenban": "quarantine",
                "api-mintavetel": "tests"
            }, inplace=True
        )

        self.df["cases"] = self.df.cases_pest.astype(int) + self.df.cases_countryside.astype(int)
        self.df["recovered"] = self.df.recovered_pest.astype(int) + self.df.recovered_countryside.astype(int)
        self.df["deaths"] = self.df.deaths_pest.astype(int) + self.df.deaths_countryside.astype(int)
        # self.df.rename(
        #     columns = {
        #         "Fertőzött": "Budapest and Pest counties",
        #         "Gyógyult": "recovered",
        #         "Elhunyt": "deaths",
        #         "Karanténban": "quarantine",
        #         "Mintavétel": "tests"
        #     }, inplace=True
        # )

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
