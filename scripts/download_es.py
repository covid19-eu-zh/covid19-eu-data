import datetime
import os
import click

import pandas as pd
from loguru import logger

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator, get_response

DAILY_FOLDER = os.path.join("dataset", "daily", "es")

# This is the most useful
CCAA_DATA = "https://cnecovid.isciii.es/covid19/resources/casos_diagnostico_ccaa.csv"
PROVINCE_DATA = "https://cnecovid.isciii.es/covid19/resources/casos_diagnostico_provincia.csv"


class SARSCOV2ES(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None, selected_date=None):
        if url is None:
            url = PROVINCE_DATA

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="ES", daily_folder=daily_folder)

        if isinstance(selected_date, str):
            selected_date = pd.to_datetime(selected_date)
        self.selected_date = selected_date

        self.use_geo = "nuts_3"

    def _get_req(self):
        pass

    def extract_table(self, dataframe=None):
        """Load data table from web page
        """



        if dataframe is None:
            dataframe = pd.read_csv(self.url)

        self.df = dataframe.copy()

        self.df.rename(
            columns = {
                "ccaa_iso": "nuts_2",
                "provincia_iso": "nuts_3",
                "fecha": "datetime",
                "num_casos": "cases_new"
            },
            inplace=True
        )

        self.df["datetime"] = pd.to_datetime(self.df["datetime"])

        if self.selected_date is None:
            self.selected_date = self.df["datetime"].max()

        self.df = self.df.loc[
            (
                self.df["datetime"] <= self.selected_date
            )
        ]

        total = []
        for i in self.df[self.use_geo].unique():
            i_sum = self.df.loc[self.df[self.use_geo] == i].cases_new.sum()
            total.append(
                {
                    "datetime": self.selected_date,
                    self.use_geo: i,
                    "cases": i_sum
                }
            )

        self.df = pd.DataFrame(total).dropna(subset=[self.use_geo])

        logger.info("list of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """

        # self.dt = dt_from_re
        self.dt = self.selected_date

    def post_processing(self):

        self.df = self.df[["country", self.use_geo, "cases", "datetime"]]

        self.df.sort_values(by="cases", inplace=True)

    def workflow(self, enable_cache=None, dataframe=None):
        """workflow connects the pipes
        """
        if enable_cache is None:
            enable_cache = False

        # extract data table from the webpage
        self.extract_table(dataframe=dataframe)
        # extract datetime from webpage
        self.extract_datetime()
        self.calculate_datetime()
        # attach a datetime column to dataframe
        self.add_datetime_to_df()
        self.add_country_to_df()
        # post processing
        self.post_processing()
        # save
        self.cache(enable_cache=enable_cache)


@click.command()
@click.option('--begin', type=click.DateTime(), help='Start of daterange')
@click.option('--end', type=click.DateTime(), help='End of daterange')
def download(begin, end):

    if begin or end:
        logger.info(f"Retrieving data between {begin} and {end}...")
        df = pd.read_csv(PROVINCE_DATA)
        if (begin is not None) and (end is None):
            mask = (
                pd.to_datetime(df["fecha"]) >= begin
            )
        elif (begin is not None) and (end is not None):
            mask = (
                pd.to_datetime(df["fecha"]) >= begin
            ) & (
                pd.to_datetime(df["fecha"]) <= end
            )

        else:
            raise Exception("Please specify begin date")

        dates = pd.to_datetime(df.loc[mask]["fecha"].unique()).sort_values()

        for date in dates:
            logger.info(f"Downloading {date} ...")
            cov_es = SARSCOV2ES(selected_date=date)
            cov_es.workflow(dataframe=df)
            if cov_es.df.empty:
                logger.error("Empty dataframe for ES data")

    else:
        cov_es = SARSCOV2ES()
        cov_es.workflow()

        logger.info(cov_es.df)
        if cov_es.df.empty:
            raise Exception("Empty dataframe for ES data")

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="ES"
    )
    da.workflow()


if __name__ == "__main__":

    download()

    print("End of Game")
