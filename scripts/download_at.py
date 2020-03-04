import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html

logging.basicConfig()
logger = logging.getLogger("sars-cov-2-germany.download")

class SARSCOV2DE():
    def __init__(self, url=None, base_folder=None):
        if url is None:
            url = "https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Fallzahlen.html"

        if base_folder is None:
            base_folder = os.path.join("dataset", "daily")

        self.base_folder = base_folder
        self.url = url
        self.req = self._get_req()

    def _get_req(self):
        try:
            req = requests.get(self.url)
        except Exception as e:
            raise Exception(e)

        return req

    def extract_table(self):
        """Load data table from web page
        """
        req_dfs = pd.read_html(self.req.content, flavor='lxml')

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0]
        logger.info("de cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        re_dt = re.compile(r'\(Datenstand: (\d{1,2}.\d{1,2}.\d{4}, \d{2}:\d{2}) Uhr\)')
        dt_from_re = re_dt.findall(self.req.text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.datetime = dt_from_re.isoformat()
        self.timestamp = dt_from_re.timestamp()
        self.date = dt_from_re.date().isoformat()
        self.hour = dt_from_re.hour

        logger.info(f"datetime: {self.datetime}")

    def add_datetime_to_df(self):
        """Attach a datetime column to the data
        """

        self.df["datetime"] = self.datetime

    def post_processing(self):

        self.df.rename(
            columns={
                "Fälle": "cases",
                "Bundesland": "state"
            },
            inplace=True
        )

        self.df.sort_values(by="cases", inplace=True)
        self.df.replace("Gesamt", "sum", inplace=True)

    def cache(self):
        self.df.to_csv(f"{self.base_folder}/de_covid19_{self.date}_{self.hour:0.0f}.csv", index=False)

    def workflow(self):
        """workflow connect the pipes
        """

        # extract data table from the webpage
        self.extract_table()
        # extract datetime from webpage
        self.extract_datetime()
        # attach a datetime column to dataframe
        self.add_datetime_to_df()
        # post processing
        self.post_processing()
        # save
        self.cache()

class DailyAggregator():
    def __init__(self, base_folder=None, daily_folder=None, file_path=None):
        if base_folder is None:
            base_folder = "dataset"
        if daily_folder is None:
            daily_folder = os.path.join(base_folder, "daily")
        if file_path is None:
            file_path = os.path.join(
                base_folder,
                "covid-19-de.csv"
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

    def cache(self):
        self.df.to_csv(
            self.file_path,
            index=False
        )

    def workflow(self):

        self.aggregate_daily()
        self.cache()


if __name__ == "__main__":
    cov_de = SARSCOV2DE()
    cov_de.workflow()

    print(cov_de.df)

    da = DailyAggregator()
    da.workflow()

    print("End of Game")
