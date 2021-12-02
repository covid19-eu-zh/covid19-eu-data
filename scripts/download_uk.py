import datetime
import os
import click
from numpy.core.fromnumeric import trace

import pandas as pd
from loguru import logger

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator, get_response

DAILY_FOLDER = os.path.join("dataset", "daily", "uk")

# This is the most useful
# https://api.coronavirus.data.gov.uk/v2/data?areaType=region&metric=cumCasesBySpecimenDate&metric=cumCasesBySpecimenDateRate&metric=cumDeathsByDeathDate&metric=cumVirusTests&metric=cumDeathsByDeathDateRate&format=csv
REGION_ARCHIVE_API = "https://api.coronavirus.data.gov.uk/v2/data?areaType=region&metric=cumCasesBySpecimenDate&metric=cumCasesBySpecimenDateRate&metric=cumDeathsByDeathDate&metric=cumVirusTestsByPublishDate&metric=cumDeathsByDeathDateRate&format=csv"
NATION_ARCHIVE_API = "https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&metric=cumCasesBySpecimenDate&metric=cumCasesBySpecimenDateRate&metric=cumDeathsByDeathDate&metric=cumVirusTestsByPublishDate&metric=cumDeathsByDeathDateRate&format=csv"

REGION_LATEST_API = "https://api.coronavirus.data.gov.uk/v2/data?areaType=region&metric=cumCasesBySpecimenDate&metric=cumCasesBySpecimenDateRate&metric=cumDeathsByDeathDate&metric=cumVirusTests&metric=cumDeathsByDeathDateRate&format=csv"
NATION_LATEST_API = "https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&metric=cumCasesBySpecimenDate&metric=cumCasesBySpecimenDateRate&metric=cumDeathsByDeathDate&metric=cumVirusTests&metric=cumDeathsByDeathDateRate&format=csv"


def get_dataframe(nation_url, region_url):

    df_nation = pd.read_csv(nation_url)
    df_region = pd.read_csv(region_url)

    df_nation = df_nation.loc[df_nation.areaName != "England"]
    df = pd.concat([df_nation, df_region])

    return df



class SARSCOV2UK(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None, selected_date=None):
        if url is None:
            logger.warning("Please specify dataframe for workflow")
            url = NATION_LATEST_API

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="UK", daily_folder=daily_folder)

        if isinstance(selected_date, str):
            selected_date = pd.to_datetime(selected_date)
        self.selected_date = selected_date

        self.use_geo = "nuts_1"

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
                "areaName": self.use_geo,
                "date": "datetime",
                "cumCasesBySpecimenDate": "cases",
                "cumCasesBySpecimenDateRate": "cases/100k pop.",
                "cumDeathsByDeathDate": "deaths",
                "cumDeathsByDeathDateRate": "deaths/100k pop.",
                # "cumVirusTests": "tests",
                "cumVirusTestsByPublishDate": "tests",
            },
            inplace=True
        )

        self.df["datetime"] = pd.to_datetime(self.df["datetime"])

        if self.selected_date is None:
            # max_date = []
            # for nut in self.df.nuts_1:
            #     max_date.append(
            #         self.df.loc[
            #             self.df.nuts_1 == nut
            #         ]["datetime"].max()
            #     )
            # self.selected_date = min(max_date)
            self.selected_date = self.df["datetime"].max()

        self.df = self.df.loc[
            (
                self.df["datetime"] <= self.selected_date
            ) & (
                self.df["datetime"] >= self.selected_date
            )
        ]
        self.df = self.df.fillna(0)[
            [
                'datetime', self.use_geo, 'cases', 'cases/100k pop.',
                'deaths', 
                'tests',
                'deaths/100k pop.'
            ]
        ]

        logger.info("list of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """

        # self.dt = dt_from_re
        self.dt = self.selected_date

    def post_processing(self):

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
@click.option('--traceback', type=int, default=14, help='Number of days to trace back')
def download(begin, end, traceback):
    if begin is None:
        logger.info(f"Trace back {traceback} days")
        begin = pd.to_datetime(
            datetime.date.today() - datetime.timedelta(traceback)
        )

    if begin or end:
        df = get_dataframe(
            nation_url=NATION_ARCHIVE_API, region_url=REGION_ARCHIVE_API
        )

        logger.info(f"Retrieving data between {begin} and {end}...")

        if (begin is not None) and (end is None):
            mask = (
                pd.to_datetime(df["date"]) >= begin
            )
        elif (begin is not None) and (end is not None):
            mask = (
                pd.to_datetime(df["date"]) >= begin
            ) & (
                pd.to_datetime(df["date"]) <= end
            )
        else:
            raise Exception("Please specify begin date")

        df = df.loc[mask]

        dates = pd.to_datetime(df["date"].unique()).sort_values()

        for date in dates:
            logger.info(f"Downloading {date} ...")
            cov_uk = SARSCOV2UK(selected_date=date)
            cov_uk.workflow(dataframe=df)
            if cov_uk.df.empty:
                logger.error("Empty dataframe for UK data")

    # else:
    #     # the latest API has missing data.
    #     # kind of makes sense since some departments report data quite late.
    #     df = get_dataframe(
    #         nation_url=NATION_LATEST_API, region_url=REGION_LATEST_API
    #         # nation_url=NATION_ARCHIVE_API, region_url=REGION_ARCHIVE_API
    #     )
    #     cov_uk = SARSCOV2UK()
    #     cov_uk.workflow(dataframe=df)

    #     logger.info(cov_uk.df)
    #     if cov_uk.df.empty:
    #         raise Exception("Empty dataframe for UK data")

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="UK"
    )
    da.workflow()


if __name__ == "__main__":

    download()

    print("End of Game")
