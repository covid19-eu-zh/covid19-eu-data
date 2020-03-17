import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.de")

RKI_REPORT_URL = "https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Fallzahlen.html"
DAILY_FOLDER = os.path.join("dataset", "daily", "de")

class SARSCOV2DE(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = RKI_REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="DE", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """
        req_dfs = pd.read_html(
            self.req.content, flavor='lxml',
            decimal=","
        )

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0]#[["Bundesland","Zahl be­stä­tig­ter Fälle (darunter Todes­fälle)"]]
        self.df.columns = self.df.columns.droplevel(0)

        logger.info("de cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        re_dt = re.compile(r'.tand: (\d{1,2}.\d{1,2}.\d{4}, \d{1,2}:\d{2}) Uhr')
        dt_from_re = re_dt.findall(self.req.text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):
        self.df.drop(
            ["Unnamed: 5_level_1", "Dif­fe­renz zum Vor­tag"], axis=1,
            inplace=True
        )
        self.df.rename(
            columns={
                "Unnamed: 0_level_1": "state",
                "An­zahl": "cases",
                "Erkr./ 100.000 Einw.": "cases/100k pop.",
                "Todes­fälle": "deaths",
                "Todes\xadfälle": "deaths"
            },
            inplace=True
        )

        self.df.fillna(0, inplace=True)

        self.df["deaths"] = self.df.deaths.astype(int)

        self.df.replace(
            "Schleswig Holstein", "Schleswig-Holstein",
            inplace=True
        )

        self.df.sort_values(by="cases", inplace=True)
        self.df.replace("Gesamt", "sum", inplace=True)


if __name__ == "__main__":
    cov_de = SARSCOV2DE()
    cov_de.workflow()

    print(cov_de.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="DE"
    )
    da.workflow()

    print("End of Game")
