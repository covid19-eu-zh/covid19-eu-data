import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.fr")

REPORT_URL = "https://www.santepubliquefrance.fr/maladies-et-traumatismes/maladies-et-infections-respiratoires/infection-a-coronavirus/articles/infection-au-nouveau-coronavirus-sars-cov-2-covid-19-france-et-monde"
DAILY_FOLDER = os.path.join("dataset", "daily", "fr")

class SARSCOV2DE(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="FR", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """
        req_dfs = pd.read_html(self.req.content, flavor='lxml')

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0][["Région de notification","Cas confirmés"]]
        logger.info("records cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        Nombre de cas rapportés par région au 10/03/2020 à 15h (données Santé publique France)
        """
        re_dt = re.compile(r'au (\d{1,2}/\d{1,2}/\d{4}) &agrave; (\d{1,2}h) \(')
        dt_from_re = re_dt.findall(self.req.text)
        print(dt_from_re)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        dt_from_re = " ".join(dt_from_re)
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.rename(
            columns={
                "Région de notification": "authority",
                "Cas confirmés": "cases"
            },
            inplace=True
        )

        self.df.sort_values(by="cases", inplace=True)
        self.df.replace("Total Outre Mer", "sum", inplace=True)
        self.df.replace("Total Métropole", "sum", inplace=True)


if __name__ == "__main__":
    cov_de = SARSCOV2DE()
    cov_de.workflow()

    print(cov_de.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="fr"
    )
    da.workflow()

    print("End of Game")
