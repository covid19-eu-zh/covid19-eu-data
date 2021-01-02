import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.se")

SE_REPORT_URL = "https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/aktuellt-epidemiologiskt-lage/"
DAILY_FOLDER = os.path.join("dataset", "daily", "se")

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
        req_dfs = pd.read_html(self.req.content, flavor='lxml')

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0].rename(lambda x:x.replace('*', ''), axis='columns') # there is another list, req_dfs[1], contains source of cases

        self.df["nuts_3"] = self.df["Region"].apply(lambda x:x.replace('*',''))
        self.df["cases"] = self.df["Fall"].apply(lambda x:int(x.replace(' ','')))
        self.df["cases/100k pop."] = self.df["Kumulativ Incidens"].astype(float)
        self.df["percent"] = self.df["Procent"].astype(float)

        logger.info("se cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """
        re_dt = re.compile(r'Sverige \d{1,2} \w{0,5} \d{4} \(kl. \d{1,2}.\d{2}\)')
        dt_from_re = re_dt.findall(self.req.text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        re_sub = re.compile('Sverige\ |(\(|\)|kl.\ )')
        dt_from_re = re_sub.sub('', dt_from_re.replace('.',':').replace('Mars','March')) # need to find a better way to transfer month
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

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

    cov_se = SARSCOV2SE()
    cov_se.workflow()

    print(cov_se.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="SE"
    )
    da.workflow()

    print("End of Game")
