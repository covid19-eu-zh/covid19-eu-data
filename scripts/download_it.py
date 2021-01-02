import click
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
logger = logging.getLogger("covid-eu-data.download.it")

FULL_REPORT_URL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province.json"
REPORT_URL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province-latest.json"
DAILY_FOLDER = os.path.join("dataset", "daily", "it")


class SARSCOV2IT(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="IT", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        self.df = pd.read_json(self.url)
        # Get datetime
        self.dt = dateutil.parser.parse(self.df.data.unique()[0])

        select_cols = {
            "denominazione_regione": "nuts_2",
            "denominazione_provincia": "nuts_3",
            "totale_casi": "cases"
        }
        self.df = self.df[list(select_cols.keys())]
        self.df.rename(columns=select_cols, inplace=True)
        self.df.replace("In fase di definizione/aggiornamento", "unassigned", inplace=True)

        logger.info("list of cases:\n", self.df)

    def post_processing(self):

        # add sum
        # total = self.df.cases.sum()
        # self.df = self.df.append(
        #     pd.DataFrame(
        #         [[self.country, "sum", "", total, self.datetime]],
        #         columns=["country", "nuts_2", "nuts_3", "cases", "datetime"]
        #     )
        # )

        self.df.sort_values(by="cases", inplace=True)


class SARSCOV2ITFULL(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = FULL_REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="IT", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        self.df = pd.read_json(self.url)
        # Get datetime
        self.dt = dateutil.parser.parse(self.df.data.unique()[0])

        select_cols = {
            "data": "datetime",
            "denominazione_regione": "nuts_2",
            "denominazione_provincia": "nuts_3",
            "totale_casi": "cases"
        }
        self.df = self.df[list(select_cols.keys())]
        self.df.rename(columns=select_cols, inplace=True)
        self.df.replace("In fase di definizione/aggiornamento", "unassigned", inplace=True)
        self.df['datetime'] = self.df.datetime.apply(lambda x: dateutil.parser.parse(x).isoformat())
        self.df['country'] = self.country

        logger.info("list of cases:\n", self.df)

    def _daily_sum(self, df, dt):
        # add sum
        df_copy = df.copy()
        total = df_copy.cases.sum()
        df_copy = df_copy.append(
            pd.DataFrame(
                [[self.country, "sum", "", total, dt]],
                columns=["country", "nuts_2", "nuts_3", "cases", "datetime"]
            )
        )
        return df_copy

    def save_daily(self):

        for dt in self.df.datetime.unique():
            dt_datetime = dateutil.parser.parse(dt)
            date = dt_datetime.date().isoformat()
            hour = dt_datetime.hour
            minute = dt_datetime.minute

            df_dt = self.df.loc[
                self.df.datetime == dt
            ]
            # df_dt = self._daily_sum(df_dt, dt)
            df_dt.sort_values(by="cases", inplace=True)

            dt_path = f"{self.daily_folder}/it_covid19_{date}_{hour:0.0f}_{minute:02.0f}.csv"
            df_dt = df_dt[
                [i for i in _COLUMNS_ORDER if i in self.df.columns]
            ]
            df_dt.to_csv(
                dt_path,
                index=False
            )

    def workflow(self):

        self.extract_table()
        self.save_daily()


@click.command()
@click.option(
    '-f', '--full', flag_value='full',
    default=False, help='Use to download and process cases for all dataes.'
)
def download(full):
    if full:
        logger.info("Download full data")
        cov_it_full = SARSCOV2ITFULL()
        cov_it_full.workflow()

    cov_it = SARSCOV2IT()
    cov_it.workflow()

    logger.info(cov_it.df)
    if cov_it.df.empty:
        raise Exception("Empty data for IT data")

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="IT"
    )
    da.workflow()


if __name__ == "__main__":

    download()

    print("End of Game")
