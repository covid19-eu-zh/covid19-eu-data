import logging
import os
import re

import datetime
import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files, get_response)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.se")

SE_REPORT_URL = "https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/aktuellt-epidemiologiskt-lage/"
DAILY_FOLDER = os.path.join("dataset", "daily", "se")

TOTAL_API = "https://services5.arcgis.com/fsYDFeRKu1hELJJs/arcgis/rest/services/FOHM_Covid_19_FME_1/FeatureServer/3/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Totalt_antal_fall%22%2C%22outStatisticFieldName%22%3A%22value%22%7D%5D&cacheHint=true"
INTENSIVE_API = "https://services5.arcgis.com/fsYDFeRKu1hELJJs/arcgis/rest/services/FOHM_Covid_19_FME_1/FeatureServer/3/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Totalt_antal_intensivv%C3%A5rdade%22%2C%22outStatisticFieldName%22%3A%22value%22%7D%5D&cacheHint=true"
DEATHS_API = "https://services5.arcgis.com/fsYDFeRKu1hELJJs/arcgis/rest/services/FOHM_Covid_19_FME_1/FeatureServer/3/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Totalt_antal_avlidna%22%2C%22outStatisticFieldName%22%3A%22value%22%7D%5D&cacheHint=true"
DAILY_DIFF_REGION_TIMESERIES_API = "https://services5.arcgis.com/fsYDFeRKu1hELJJs/arcgis/rest/services/FOHM_Covid_19_FME_1/FeatureServer/1/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&orderByFields=Statistikdatum%20desc&resultOffset=0&resultRecordCount=2000&cacheHint=true"
# This is the most useful
REGION_LATEST_API = "https://services5.arcgis.com/fsYDFeRKu1hELJJs/arcgis/rest/services/FOHM_Covid_19_FME_1/FeatureServer/0/query?f=json&where=Region%20%3C%3E%20%27dummy%27&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&orderByFields=Region%20asc&outSR=102100&resultOffset=0&resultRecordCount=25&cacheHint=true"

class SARSCOV2SE(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = SE_REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="SE", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        data = self.req.json()['features']
        data = [i['attributes'] for i in data]
        self.df = pd.DataFrame(data)

        self.df.rename(
            columns = {
                "Region": "nuts_3",
                "Totalt_antal_fall": "cases",
                "Fall_per_100000_inv": "cases/100k pop.",
                "Totalt_antal_intensivvårdade": "intensive_care",
                "Totalt_antal_avlidna": "deaths"
            },
            inplace=True
        )

        logger.info("se cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        req = get_response(DAILY_DIFF_REGION_TIMESERIES_API)
        data = req.json()['features']
        dates = [i['attributes']['Statistikdatum'] for i in data]
        dates.sort()
        timestamp = dates[-1]
        self.dt = datetime.datetime.fromtimestamp(timestamp/1000)

        logger.info("using date")

    def post_processing(self):
        self.df.fillna(0, inplace=True)

        self.df.sort_values(by="cases", inplace=True)
        self.df.replace("Totalt", "sum", inplace=True)

        self.df.drop(
            self.df.loc[
                self.df['nuts_3'] == 'sum'
            ].index,
            inplace=True
        )

if __name__ == "__main__":

    # column_converter = {
    #     "authority": "nuts_3"
    # }
    # drop_rows = {
    #     "authority": "sum"
    # }

    # daily_files = retrieve_files(DAILY_FOLDER)
    # daily_files.sort()

    # for file in daily_files:
    #     file_path = os.path.join(DAILY_FOLDER, file)
    #     file_transformation = DailyTransformation(
    #         file_path=file_path,
    #         column_converter=column_converter,
    #         drop_rows=drop_rows
    #     )
    #     file_transformation.workflow()

    cov_se = SARSCOV2SE(url=REGION_LATEST_API)
    cov_se.workflow()

    print(cov_se.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="SE"
    )
    da.workflow()

    print("End of Game")
