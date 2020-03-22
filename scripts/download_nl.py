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
logger = logging.getLogger("covid-eu-data.download.nl")

REPORT_URL = "https://www.volksgezondheidenzorg.info/onderwerp/infectieziekten/regionaal-internationaal/coronavirus-covid-19#node-coronavirus-covid-19-meldingen"
REPORT_CSV_BASE_URL = "https://www.volksgezondheidenzorg.info"
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
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="NL", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        doc = lxml.html.document_fromstring(self.req.text)
        el = doc.xpath('.//div[@id="csvData"]')
        if el:
            text = "".join(
                el[0].xpath('.//text()')
            )

        self.df = pd.read_csv(
            io.StringIO(text), sep=";", skiprows=[1,2], header=None
        )
        self.df = self.df[[0, 1, 2, 3, 4]]
        cols = text.split("\n")[1].split(";")
        self.df.columns = cols
        df_other = self.df.loc[self.df.Gemnr == -1]
        df_other.Gemeente = "Other"

        self.df = self.df.loc[
            self.df.Gemnr >= 0
        ]
        self.df = pd.concat([self.df, df_other])

        original_cols = ["Gemeente", "Aantal", "BevAant", "Aantal per 100.000 inwoners"]
        self.df = self.df[original_cols]
        self.df.fillna(0, inplace=True)
        self.df["Aantal"] = self.df.Aantal.astype(int)
        # add sum
        # total = self.df.Aantal.sum()
        # total_pop = self.df["BevAant"].sum()
        # self.df = self.df.append(
        #     pd.DataFrame(
        #         [["sum", total, total_pop, f"{total/total_pop:0.2f}"]], columns=original_cols
        #     )
        # )

        logger.info("list of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """

        doc = lxml.html.document_fromstring(self.req.text)
        el = doc.xpath('.//div[@id="csvData"]')
        if el:
            text = "".join(
                el[0].xpath('.//text()')
            )
        # <p>aantal per 17 maart 2020 14.00 uur</p>
        re_dt = re.compile(r"<p>aantal per (.*)uur</p>")
        dt_from_re = re_dt.findall(self.req.content.decode("utf-8"))

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0].replace("\xa0", " ")
        for key in DUTCH_MONTHS_TO_EN:
            if key in dt_from_re:
                dt_from_re = dt_from_re.replace(key, DUTCH_MONTHS_TO_EN[key])
                break
        dt_from_re = dateutil.parser.parse(dt_from_re.replace(".", ":"))
        self.dt = dt_from_re

    def post_processing(self):

        self.df.rename(
            columns={
                "Gemeente": "lau",
                "Aantal": "cases",
                "BevAant": "population",
                "Aantal per 100.000 inwoners": "cases/100k pop."
            },
            inplace=True
        )

        self.df = self.df[["country", "lau", "cases", "population", "cases/100k pop.", "datetime"]]

        self.df.sort_values(by="cases", inplace=True)


if __name__ == "__main__":
    column_converter = {
        "city": "lau"
    }
    drop_rows = {
        "city": "sum"
    }

    daily_files = retrieve_files(DAILY_FOLDER)
    daily_files.sort()

    for file in daily_files:
        file_path = os.path.join(DAILY_FOLDER, file)
        file_transformation = DailyTransformation(
            file_path=file_path,
            column_converter=column_converter,
            drop_rows=drop_rows
        )
        file_transformation.workflow()

    cov_nl = SARSCOV2NL()
    cov_nl.workflow()

    print(cov_nl.df)
    if cov_nl.df.empty:
        raise Exception("Empty dataframe for NL data")

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="NL"
    )
    da.workflow()

    print("End of Game")
