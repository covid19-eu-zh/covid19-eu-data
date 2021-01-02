import datetime
import os

import pandas as pd
from loguru import logger

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator, get_response

DAILY_FOLDER = os.path.join("dataset", "daily", "fi")

# This is the most useful
REGION_LATEST_API = "https://services7.arcgis.com/nuPvVz1HGGfa0Eh7/arcgis/rest/services/korona_tapaukset_kumulatiivisesti_kunnittain/FeatureServer/0/query?f=json&where=tapauksia_yhteensa%3E1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&orderByFields=kunta%20asc&resultOffset=0&resultRecordCount=500&resultType=standard&cacheHint=true"


class SARSCOV2FI(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REGION_LATEST_API

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="FI", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        data = self.req.json()['features']
        data = [i['attributes'] for i in data]
        self.df = pd.DataFrame(data)

        self.df.rename(
            columns = {
                "date": "datetime",
                "tapauksia": "cases_new",
                "tapauksia_yhteensa": "cases",
                "Vaesto": "population",
                "Ilmaantuvuus": "cases/100k pop.",
                # "testimaara_yhteensa": "tests",
                # "testimaara_suhde": "tests/100k pop.",
                "kunta": "lau"
            },
            inplace=True
        )

        self.df["datetime"] = pd.to_datetime(self.df["datetime"] * 1e6).dt.round("H")

        logger.info("se cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        self.dt = self.df["datetime"].max()
        logger.info(f"using datetime: {self.dt}")

    def post_processing(self):
        self.df.fillna(0, inplace=True)

        self.df.sort_values(by="cases", inplace=True)


if __name__ == "__main__":

    cov_fi = SARSCOV2FI(url=REGION_LATEST_API)
    cov_fi.workflow()

    logger.info(
        "\n",cov_fi.df
    )

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="FI"
    )
    da.workflow()

    print("End of Game")
