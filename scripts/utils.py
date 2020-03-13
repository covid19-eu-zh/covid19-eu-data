import datetime
import logging
import os
import re
from abc import abstractmethod

import dateutil
import pandas as pd
import requests
from lxml import etree, html

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.util")

_COLUMNS_ORDER = [
    "country", "authority", "state", "city",
    "cases", "cases_lower", "cases_upper", "cases_raw", "recovered", "deaths",
    "datetime"
]


class COVIDScrapper():
    def __init__(self, url, country, daily_folder=None):
        if not url:
            raise Exception("Please specify url!")
        if not country:
            raise Exception("Please specify country")

        self.country = country

        if daily_folder is None:
            daily_folder = os.path.join("dataset", "daily", f"{self.country.lower()}")

        self.daily_folder = daily_folder
        self.url = url
        self.req = self._get_req()
        try:
            os.makedirs(self.daily_folder)
        except FileExistsError as e:
            logger.info(f"{self.daily_folder} already exists, no need to create folder")
            pass

    def _get_req(self):
        try:
            req = requests.get(self.url)
        except Exception as e:
            raise Exception(e)

        return req

    @abstractmethod
    def extract_table(self):
        """Load data table from web page
        """

    @abstractmethod
    def extract_datetime(self):
        """Get datetime of dataset and assign datetime obj to self.dt
        """

    def calculate_datetime(self):

        self.datetime = self.dt.isoformat()
        self.timestamp = self.dt.timestamp()
        self.date = self.dt.date().isoformat()
        self.hour = self.dt.hour
        self.minute = self.dt.minute

        logger.info(f"datetime: {self.datetime}")

    def add_datetime_to_df(self):
        """Attach a datetime column to the data
        """

        self.df["datetime"] = self.datetime

    def add_country_to_df(self):

        self.df["country"] = self.country

    @abstractmethod
    def post_processing(self):
        """clean up the dataframe: state, cases, datetime
        """

    def cache(self):
        self.df = self.df[
            [i for i in _COLUMNS_ORDER if i in self.df.columns]
        ]
        self.df.to_csv(
            f"{self.daily_folder}/{self.country.lower()}_covid19_{self.date}_{self.hour:0.0f}_{self.minute:02.0f}.csv",
            index=False
        )

    def workflow(self):
        """workflow connect the pipes
        """

        # extract data table from the webpage
        self.extract_table()
        # extract datetime from webpage
        self.extract_datetime()
        self.calculate_datetime()
        # attach a datetime column to dataframe
        self.add_datetime_to_df()
        self.add_country_to_df()
        # post processing
        self.post_processing()
        # save
        self.cache()


class DailyAggregator():
    def __init__(self, base_folder, daily_folder, country, file_path=None, fill=None):
        if base_folder is None:
            base_folder = "dataset"
        if daily_folder is None:
            raise Exception("Please specify daily folder")
        if fill is None:
            fill = True
        self.fill = fill
        if not country:
            raise Exception("Please specify country")
        self.country = country

        if file_path is None:
            file_path = os.path.join(
                base_folder,
                f"covid-19-{self.country.lower()}.csv"
            )

        self.base_folder = base_folder
        self.daily_folder = daily_folder
        self.file_path = file_path

        self.daily_files = self._retrieve_all_daily()

    def _retrieve_all_daily(self):
        """retrieve a list of files
        """

        files = os.listdir(self.daily_folder)
        if files:
            files = [i for i in files if not i.startswith(".")]

        return files

    def aggregate_daily(self):

        dfs = []
        for file in self.daily_files:
            file_path = os.path.join(self.daily_folder, file)
            dfs.append(pd.read_csv(file_path))

        self.df = pd.concat(dfs)
        self.df.sort_values(by=["datetime", "cases"], inplace=True)
        self.df.drop_duplicates(inplace=True)
        if self.fill:
            if "deaths" in self.df.columns:
                self.df["deaths"] = self.df.deaths.fillna(0).astype(int)
        self.df = self.df[
            [i for i in _COLUMNS_ORDER if i in self.df.columns]
        ]

    def cache(self):
        self.df.to_csv(
            self.file_path,
            index=False
        )

    def workflow(self):

        self.aggregate_daily()
        self.cache()
