import datetime
import os

import pandas as pd
from loguru import logger

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator, get_response

DAILY_FOLDER = os.path.join("dataset", "daily", "pt")

# This is the most useful
REGION_LATEST_API = "https://services.arcgis.com/CCZiGSEQbAxxFVh3/arcgis/rest/services/IncidenciaCOVIDporConc100k_view/FeatureServer/0/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&orderByFields=Valorincid%20desc&resultOffset=0&resultRecordCount=310&resultType=standard&cacheHint=true"


class SARSCOV2PT(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REGION_LATEST_API

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="PT", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        data = self.req.json()['features']
        data = [i['attributes'] for i in data]
        self.df = pd.DataFrame(data)

        self.df.rename(
            columns = {
                "date": "datetime",
                "Incidência": "cases",
                "Total": "population",
                "ARS": "nuts_2",
                "Distrito": "nuts_3",
                "Concelho": "lau"
            },
            inplace=True
        )

        self.df["datetime"] = pd.to_datetime(datetime.date.today())

        self.df[['nuts_2', 'nuts_3', 'population', 'lau', 'cases', 'datetime']]


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

    cov_pt = SARSCOV2PT(url=REGION_LATEST_API)
    cov_pt.workflow()

    logger.info(
        "\n",cov_pt.df
    )

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="PT"
    )
    da.workflow()

    print("End of Game")
