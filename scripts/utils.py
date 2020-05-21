import datetime
import json
import logging
import os
import random
import re
from abc import abstractmethod

import dateutil
import pandas as pd
import requests
from lxml import etree, html
from lxml.html import fromstring
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.util")

_COLUMNS_ORDER = [
    "country", "region", "authority", "state", "county", "city", "province",
    "nuts_1", "nuts_2", "nuts_3", "lau",
    "nuts_1_code", "nuts_2_code", "nuts_3_code", "lau_code",
    "cases", "cases_lower", "cases_upper", "cases_raw",
    "population", "cases/100k pop.", "percent",
    "recovered", "deaths",
    "tests", "tests_positive", "quarantine", "hospitalized", "hospitalized/100k pop.",
    "intensive_care",
    "datetime"
]


class COVIDScrapper():
    def __init__(self, url, country, daily_folder=None, cache_format=None):
        """
        COVIDScrapper is the base class to scrape data from remote resources.

        :param url: url to the remote resource
        :type url: str
        :param country: Alpha 2 code of the country
        :type country: str
        :param daily_folder: folder where the daily updates are being stored
        :type daily_folder: str, optional
        """
        if not url:
            raise Exception("Please specify url!")
        if not country:
            raise Exception("Please specify country")
        if cache_format is None:
            cache_format = 'html'

        self.cache_format = cache_format

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
        """
        _get_req get the responses from the remote web page.

        :return: requests object
        """
        try:
            req = get_response(self.url)
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
        """
        calculate_datetime formats and decomposes the datetime
        """
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
        """
        add_country_to_df adds a column country to the dataframe
        """
        self.df["country"] = self.country

    @abstractmethod
    def post_processing(self):
        """clean up the dataframe: state, cases, datetime
        """

    def cache(self):
        """
        cache sorts the dataframes and saves the dataframe as csv.
        """
        self.df = self.df[
            [i for i in _COLUMNS_ORDER if i in self.df.columns]
        ]
        self.df.to_csv(
            f"{self.daily_folder}/{self.country.lower()}_covid19_{self.date}_{self.hour:0.0f}_{self.minute:02.0f}.csv",
            index=False
        )

        try:
            if "/" in self.daily_folder:
                daily_folder_sub = self.daily_folder.split("/")[-1]
            elif "\\" in self.daily_folder:
                daily_folder_sub = self.daily_folder.split("\\")[-1]
            else:
                raise Exception("Could not determine the sub folders")

            cache_folder = os.path.join(
                self.daily_folder,
                "../../../cache/daily",
                daily_folder_sub
            )
            os.makedirs(
                cache_folder
            )
        except FileExistsError as e:
            logger.info(f"{cache_folder} already exists, no need to create folder")
            pass

        with open(
            os.path.join(cache_folder, f"{self.dt.strftime('%Y%m%d%H%M')}.{self.cache_format}"),
            'wb'
        ) as f:
            f.write(self.req.content)


    def workflow(self):
        """workflow connects the pipes
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
    def __init__(self, base_folder, daily_folder, country, file_path=None, fill=None, replace=None):
        """
        DailyAggregator aggregates the daily updates and save them as one file.

        :param base_folder: where the whole tabular dataset is being stored
        :type base_folder: str
        :param daily_folder: where the daily data is being stored
        :type daily_folder: str
        :param country: alpha 2 code of the country.
        :type country: str
        :param file_path: destination of the aggregated file
        :type file_path: str, optional
        :param fill: whether to fill the missing data
        :type fill: bool, optional
        """
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
        self.replace_dict = replace

    def _retrieve_all_daily(self):
        """retrieve a list of files
        """

        files = os.listdir(self.daily_folder)
        if files:
            files = [i for i in files if not i.startswith(".")]

        return files

    def aggregate_daily(self):
        """
        aggregate_daily aggretates the daily updates into one dataframe
        """
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

        int_cols = [
            "hospitalized", "recovered", "deaths", "intensive_care",
            "tests", "tests_positive", "quarantine"
        ]
        for col in int_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].apply(
                    lambda x: int(x) if not pd.isna(x) else ''
                )

        self.df = self.df[
            [i for i in _COLUMNS_ORDER if i in self.df.columns]
        ]

    def replace(self):

        self.df.replace(self.replace_dict,inplace=True)

    def cache(self):
        """
        cache saves the dataframe as a csv file
        """
        self.df.to_csv(
            self.file_path,
            index=False
        )

    def workflow(self):
        """
        workflow connects the pipes
        """
        self.aggregate_daily()
        if self.replace_dict:
            self.replace()
        self.cache()


class DailyTransformation():
    def __init__(self, file_path, column_converter=None, drop_rows=None):
        """
        DailyTransformation is a legacy data transformation tool.

        :param file_path: destination of the aggregated file
        :type file_path: str, optional
        :param column_converter: dict used to rename columns
        :type column_converter: dict
        :param drop_row: dict used to rename columns
        :type drop_row: dict
        """
        if column_converter is None:
            column_converter = {}
        if drop_rows is None:
            drop_rows = {}

        self.drop_rows = drop_rows
        self.column_converter = column_converter
        self.file_path = file_path

    def transform_daily(self):
        """
        aggregate_daily aggretates the daily updates into one dataframe
        """

        self.df = pd.read_csv(self.file_path)

        for idx, val in self.drop_rows.items():
            if idx in self.df.columns:
                self.df.drop(
                    self.df.loc[
                        self.df[idx] == val
                    ].index,
                    inplace=True
                )

        self.df.rename(
            columns=self.column_converter,
            inplace=True
        )


    def cache(self):
        """
        cache saves the dataframe as a csv file
        """
        self.df.to_csv(
            self.file_path,
            index=False
        )

    def workflow(self):
        """
        workflow connects the pipes
        """
        self.transform_daily()
        self.cache()


def retrieve_files(daily_folder, filetype=None):
        """retrieve a list of files
        """
        if filetype is None:
            filetype = 'csv'

        files = os.listdir(daily_folder)
        if files:
            files = [
                i for i in files
                if (not i.startswith(".")) and (i.endswith(filetype))
            ]

        return files


def random_user_agent():
    """Generate random user agent for requests
    """
    user_agent_list = [
        #Chrome
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        #Firefox
        'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
    ]

    return {'User-Agent': random.choice(user_agent_list)}


def get_response(
        link, retry_params=None, headers=None, timeout=None,
        proxies=None, session=None
    ):
    """
    get_response gets the responses of the a URL.

    :param link: link to the content to be recieved
    :type link: str
    :param retry_params: rules to retry
    :type retry_params: dict, optional
    :param headers: headers for the request
    :type headers: dict, optional
    :param timeout: timeout parameters for the request
    :type timeout: tuple, optional
    :param proxies: proxies
    :type proxies: dict, optional
    :param session: a session object to be used
    :type session: requests.Session, optional
    :return: response from the url
    :rtype: requests.models.Response
    """

    if retry_params is None:
        retry_params = {}

    retry_params = {
        **{
            'retries': 5,
            'backoff_factor': 0.3,
            'status_forcelist': (500, 502, 504)
        },
        **retry_params
    }

    if headers is None:
        headers = random_user_agent()

    if timeout is None:
        timeout = (5, 14)

    if session is None:
        session = requests.Session()

    if proxies is None:
        proxies = {}

    retry = Retry(
        total=retry_params.get('retries'),
        read=retry_params.get('retries'),
        connect=retry_params.get('retries'),
        backoff_factor=retry_params.get('backoff_factor'),
        status_forcelist=retry_params.get('status_forcelist'),
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    page = session.get(link, headers=headers, proxies=proxies)

    status = page.status_code

    return page


def rename_cache(path, name):
    old = os.path.join(path, name)
    new = os.path.join(path, name.replace(":","").replace("-", "").replace("T",""))
    os.rename(old,new)


if __name__ == "__main__":

    cache_daily = os.path.join("cache", "daily")
    for i in os.listdir(cache_daily):
        i_path = os.path.join(cache_daily, i)
        for j in os.listdir(i_path):
            rename_cache(i_path, j)

    pass
