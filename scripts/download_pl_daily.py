import datetime
import json
import logging
import os
import re
import io

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files, get_response)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.pl")

# REPORT_URL = "https://www.gov.pl/web/koronawirus/wykaz-zarazen-koronawirusem-sars-cov-2"

REPORT_URL = "https://covid19-rcb-info.hub.arcgis.com/"
DATA_DATE_URL = "https://services9.arcgis.com/RykcEgwHWuMsJXPj/arcgis/rest/services/global_corona_actual_widok2/FeatureServer/0/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&resultOffset=0&resultRecordCount=1&resultType=standard&cacheHint=true"
# CSV_DATA_URL = "https://arcgis.com/sharing/rest/content/items/829ec9ff36bc45a88e1245a82fff4ee0/data"
CSV_DATA_URL = "https://arcgis.com/sharing/rest/content/items/153a138859bb4c418156642b5b74925b/data"
DAILY_FOLDER = os.path.join("dataset", "daily", "pl")


class SARSCOV2PL(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = CSV_DATA_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="PL", daily_folder=daily_folder)

    def extract_table_html(self):
        """Load data table from web page
        """
        doc = html.document_fromstring(self.req.content.decode('utf-8'))
        el = doc.xpath('.//pre[@id="registerData"]')
        if el:
            text = "".join(
                el[0].xpath('.//text()')
            )

        data = json.loads(text).get("parsedData")

        df = pd.read_json(data)

        if df.empty:
            raise Exception("Did not find data on webpage")

        self.df = df # Województwo; Liczba; Liczba zgonów; Id
        self.df.rename(
            columns = {
                "Województwo": "nuts_2",
                "Liczba": "cases",
                "Liczba zgonów": "deaths"
            },
            inplace=True
        )
        self.df.replace("Cała Polska", "sum", inplace=True)

        self.df.drop(
            self.df.loc[
                self.df['nuts_2'] == 'sum'
            ].index,
            inplace=True
        )

        # Remove space from case numbers
        self.df['cases'] = self.df['cases'].astype(str).str.replace(' ', '')

        logger.info("cases:\n", self.df)

    def extract_table(self):
        """Load data table from web page
        """

        df = pd.read_csv(io.StringIO(self.req.text), sep=';')


        if df.empty:
            raise Exception("Did not find data on webpage")

        self.df = df # Województwo; Liczba; Liczba zgonów; Id
        col_map = {
                "wojewodztwo": "nuts_2",
                "liczba_przypadkow": "cases",
                "liczba_na_10_tys_mieszkancow": "cases/100k pop.",
                "zgony": "deaths",
                "liczba_wykonanych_testow": "tests",
                "liczba_testow_z_wynikiem_pozytywnym": "tests_positive",
                "liczba_osob_objetych_kwarantanna": "quarantine"
            }
        self.df.rename(
            columns=col_map,
            inplace=True
        )
        self.df.replace("Cała Polska", "sum", inplace=True)
        self.df.replace("Cały kraj", "sum", inplace=True)
        self.df.replace("Ca³y kraj", "sum", inplace=True)

        self.df.drop(
            self.df.loc[
                self.df['nuts_2'] == 'sum'
            ].index,
            inplace=True
        )

        # Remove space from case numbers
        self.df['cases'] = self.df['cases'].astype(str).str.replace(' ', '')
        self.df = self.df[set(col_map.values()).intersection(set(self.df.columns))]

        if df['stan_rekordu_na'].unique():
            self.dt = pd.to_datetime(df['stan_rekordu_na'].unique()[0])
        else:
            raise ValueError('PL date column stan_rekordu_na has no value')

        logger.info("cases:\n", self.df)


    def extract_datetime(self):
        """Get datetime of dataset
        """
        # try:
        #     req = get_response(DATA_DATE_URL)
        # except Exception as e:
        #     raise Exception(e)

        # data = req.json().get('features')[0].get('attributes').get('DATA_SHOW')
        # dt = pd.to_datetime(data, dayfirst=True)
        # self.dt = datetime.datetime(
        #     dt.year, dt.month, dt.day
        # )
        if not self.dt:
            raise Exception("self.dt is null")

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)

    def cache(self, **kwargs):

        self.df = self.df[
            [i for i in _COLUMNS_ORDER if i in self.df.columns]
        ]
        exists = False
        for d in os.listdir(f"{self.daily_folder}"):
            df_existing = pd.read_csv(
                os.path.join(self.daily_folder, d)
            )
            if self.df.equals(df_existing):
                exists = True
                logger.info("Current data frame already exists")
                break

        if not exists:
            self.df.to_csv(
                f"{self.daily_folder}/{self.country.lower()}_covid19_{self.date}_{self.hour:0.0f}_{self.minute:02.0f}.csv",
                index=False
            )


if __name__ == "__main__":


    # column_converter = {
    #     "province": "nuts_2"
    # }
    # drop_rows = {
    #     "province": "sum"
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

    cov_pl = SARSCOV2PL()
    cov_pl.workflow()

    print(cov_pl.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="PL"
    )
    da.workflow()

    print("End of Game")
