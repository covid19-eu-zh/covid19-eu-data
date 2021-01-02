import os
from loguru import logger
import click

import pandas as pd

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files, get_response)

# REPORT_URL = "https://www.rivm.nl/coronavirus-kaart-van-nederland-per-gemeente"
REPORT_URL = "https://data.rivm.nl/covid-19/COVID-19_aantallen_gemeente_cumulatief.csv"
DAILY_FOLDER = os.path.join("dataset", "daily", "nl")
DUTCH_MONTHS_TO_EN = {
    'januari': 'january',
    'februari': 'february',
    'maart': 'march',
    'april': 'april',
    'mei': 'may',
    'juni': 'june',
    'juli': 'july',
    'augustus': 'august',
    'september': 'september',
    'oktober': 'october',
    'november': 'november',
    'december': 'december'
}

class SARSCOV2NL(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None, selected_date=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="NL", daily_folder=daily_folder)

        if isinstance(selected_date, str):
            selected_date = pd.to_datetime(selected_date)
        self.selected_date = selected_date

    def _get_req(self):
        pass

    def extract_table(self, dataframe=None):
        """Load data table from web page
        """

        if dataframe is None:
            dataframe = pd.read_csv(self.url, sep=";")

        self.df = dataframe.copy()

        # original columns: Date_of_report Municipality_code Municipality_name       Province  Total_reported  Hospital_admission  Deceased
        self.df.fillna(
            value={
                "Total_reported": 0,
                "Hospital_admission": 0,
                "Deceased": 0,
                "Municipality_name": "",
                "Province": ""
            }, inplace=True
        )

        self.df.rename(
            columns = {
                "Municipality_name": "lau",
                "Province": "nuts_2",
                "Total_reported": "cases",
                "Hospital_admission": "hospitalized",
                "Deceased": "deaths",
                "Date_of_report": "datetime"
            },
            inplace=True
        )

        def convert_int(x):
            res = None
            try:
                res = int(x)
            except Exception as e:
                logger.warning(f"{x} can not be converted to int")

            return res

        self.df["datetime"] = pd.to_datetime(self.df["datetime"])
        self.df["cases"] = self.df["cases"].apply(lambda x: convert_int(x))
        self.df["hospitalized"] = self.df["hospitalized"].apply(lambda x: convert_int(x))
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
        self.df["population"] = None

        logger.info("list of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """

        # self.dt = dt_from_re
        self.dt = self.selected_date

    def post_processing(self):

        self.df = self.df[["country", "lau", "nuts_2", "cases", "population", "hospitalized", "deaths", "datetime"]]

        self.df.sort_values(by="hospitalized", inplace=True)

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
        df = pd.read_csv(REPORT_URL, sep=";")
        if (begin is not None) and (end is None):
            mask = (
                pd.to_datetime(df["Date_of_report"]) >= begin
            )
        elif (begin is not None) and (end is not None):
            mask = (
                pd.to_datetime(df["Date_of_report"]) >= begin
            ) & (
                pd.to_datetime(df["Date_of_report"]) <= end
            )
        else:
            raise Exception("Please specify begin date")
        df = df.loc[mask]

        dates = pd.to_datetime(df["Date_of_report"].unique()).sort_values()

        for date in dates:
            logger.info(f"Downloading {date} ...")
            cov_nl = SARSCOV2NL(selected_date=date)
            cov_nl.workflow(dataframe=df)
            if cov_nl.df.empty:
                logger.error("Empty dataframe for NL data")

    else:
        cov_nl = SARSCOV2NL()
        cov_nl.workflow()

        logger.info(cov_nl.df)
        if cov_nl.df.empty:
            raise Exception("Empty dataframe for NL data")

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="NL",replace={
            "Noardeast-FryslÃ¢n": "Noardeast-Fryslân",
            "SÃºdwest-FryslÃ¢n": "Súdwest-Fryslân",
            "Súdwest Fryslân": "Súdwest-Fryslân",
            "s-Gravenhage": "'s-Gravenhage"
        }
    )
    da.workflow()


if __name__ == "__main__":

    download()

    print("End of Game")
