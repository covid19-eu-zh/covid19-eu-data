import click
import io
from loguru import logger
import os
import re

import dateutil
import lxml
import pandas as pd
import requests
from lxml import etree, html

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files)



CASES_URL = "https://raw.githubusercontent.com/iMEdD-Lab/open-data/master/COVID-19/greece_cases_v2.csv"
DEATH_URL = "https://raw.githubusercontent.com/iMEdD-Lab/open-data/master/COVID-19/greece_deaths_v2.csv"
REGION_URL = "https://raw.githubusercontent.com/iMEdD-Lab/open-data/master/COVID-19/greece_latest.csv"
DAILY_FOLDER = os.path.join("dataset", "daily", "gr")


def get_dataframes():

    df_cases = pd.read_csv(CASES_URL).drop(['Γεωγραφικό Διαμέρισμα', 'Περιφέρεια', 'county'], axis=1)
    df_deaths = pd.read_csv(DEATH_URL).drop(['Γεωγραφικό Διαμέρισμα', 'Περιφέρεια', 'county'], axis=1)
    df_region = pd.read_csv(REGION_URL)[["county_normalized", "county_en", "pop_11"]]

    cases_value_vars = [i for i in df_cases.columns.tolist() if '/' in i]
    deaths_value_vars = [i for i in df_deaths.columns.tolist() if '/' in i]

    df_cases = pd.melt(
        df_cases, id_vars=['county_normalized'], value_vars=cases_value_vars,
        var_name='datetime', value_name='cases'
    ).fillna(0)

    df_deaths = pd.melt(
        df_deaths, id_vars=['county_normalized'], value_vars=deaths_value_vars,
        var_name='datetime', value_name='deaths'
    ).fillna(0)


    df_cases["datetime"] = pd.to_datetime(df_cases["datetime"])
    df_deaths.replace("1/19/21.1", "1/19/21", inplace=True)
    df_deaths["datetime"] = pd.to_datetime(df_deaths["datetime"])

    df = pd.merge(
        df_cases, df_deaths, how="left",
        left_on=["county_normalized", "datetime"],
        right_on=["county_normalized", "datetime"]
    )

    df = pd.merge(df, df_region, how="left", left_on="county_normalized", right_on="county_normalized").drop(["county_normalized"], axis=1).rename(columns={"county_en": "nuts_3", "pop_11": "population"})


    return df


class SARSCOV2GR(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None, selected_date=None):
        if url is None:
            logger.warning("Have to specify dataframe")
            url = "nothing"

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="GR", daily_folder=daily_folder)

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
            raise Exception("Please specify a dataframe")

        self.df = dataframe.copy().fillna(0)

        if self.selected_date is None:
            self.selected_date = self.df["datetime"].max()

        def convert_int(x):
            res = None
            try:
                res = int(x)
            except Exception as e:
                logger.warning(f"{x} can not be converted to int")

            return res

        self.df["datetime"] = pd.to_datetime(self.df["datetime"])
        self.df["cases"] = self.df["cases"].apply(lambda x: convert_int(x))
        self.df["deaths"] = self.df["deaths"].apply(lambda x: convert_int(x))

        if self.selected_date is None:
            self.selected_date = self.df["datetime"].max()

        self.df = self.df.loc[
            (
                self.df["datetime"] >= self.selected_date
            ) & (
                self.df["datetime"] <= self.selected_date
            )
        ]

        logger.info("list of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """

        # self.dt = dt_from_re
        self.dt = self.selected_date

    def post_processing(self):

        self.df = self.df[["country", self.use_geo, "population", "cases", "deaths", "datetime"]]

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

    df = get_dataframes()

    if begin or end:
        logger.info(f"Retrieving data between {begin} and {end}...")

        if (begin is not None) and (end is None):
            mask = (
                pd.to_datetime(df["datetime"]) >= begin
            )
        elif (begin is not None) and (end is not None):
            mask = (
                pd.to_datetime(df["datetime"]) >= begin
            ) & (
                pd.to_datetime(df["datetime"]) <= end
            )
        else:
            raise Exception("Please specify begin date")
        df = df.loc[mask]


        dates = pd.to_datetime(df["datetime"].unique()).sort_values()

        for date in dates:
            logger.info(f"Downloading {date} ...")
            cov_gr = SARSCOV2GR(selected_date=date)
            cov_gr.workflow(dataframe=df)
            if cov_gr.df.empty:
                logger.error("Empty dataframe for GR data")

    else:
        cov_gr = SARSCOV2GR()
        cov_gr.workflow(dataframe=df)

        logger.info(cov_gr.df)
        if cov_gr.df.empty:
            raise Exception("Empty dataframe for GR data")

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="GR"
    )
    da.workflow()


if __name__ == "__main__":

    download()

    print("End of Game")
