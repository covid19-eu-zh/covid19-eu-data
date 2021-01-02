import html
import logging
import os
import re
from functools import reduce

import dateutil
import lxml
import pandas as pd
import requests
from lxml import etree

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.at")

AT_REPORT_URL = "https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html"
DAILY_FOLDER = os.path.join("dataset", "daily", "at")
AT_STATES = [
    "Burgenland",
    "Kärnten",
    "Niederösterreich",
    "Oberösterreich",
    "Salzburg",
    "Steiermark",
    "Tirol",
    "Vorarlberg",
    "Wien"
]

class SARSCOV2AT(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = AT_REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="AT", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        geo_loc_key = 'nuts_2'

        doc = lxml.html.document_fromstring(self.req.text)
        el = doc.xpath('.//main[@id="content"]')
        if el:
            paragraphs = [
                "".join(i.xpath('.//text()')) for i in el[0].xpath('.//p')
            ]
            cases_text = ""
            recovered_text = ""
            deaths_text = ""
            for par in paragraphs:
                if par.startswith("Bestätigte Fälle, "):
                    cases_text = par
                    cases_text = html.unescape(cases_text)
                elif par.startswith("Genesene Personen, "):
                    recovered_text = par
                    recovered_text = html.unescape(recovered_text)
                elif par.startswith("Todesfälle, "):
                    deaths_text = par
                    deaths_text = html.unescape(deaths_text)
        else:
            raise Exception("Could not find infobox")

        re_cases = re.compile(r'\s(\w*?)\s\((\d+)\)')
        re_deaths = re.compile(r'\s(\d+)\s\((\w+)\)')

        cases = [i for i in re_cases.findall(cases_text) if i[0] in AT_STATES]
        cases = [(s, v.replace('.','').replace(',','.')) for s,v in cases]
        recovered = [
            i for i in re_cases.findall(recovered_text) if i[0] in AT_STATES
        ]
        recovered = [(s, v.replace('.','').replace(',','.')) for s,v in recovered]
        deaths = [i for i in re_deaths.findall(deaths_text) if i[-1] in AT_STATES]
        deaths = [(v.replace('.','').replace(',','.'), s) for v, s in deaths]

        if not cases:
            raise Exception("Could not find cases_text in webpage")

        df_cases = pd.DataFrame(
            cases, columns=[geo_loc_key, "cases"]
        )

        df_recovered = pd.DataFrame(
            recovered, columns=[geo_loc_key, "recovered"]
        )
        df_deaths = pd.DataFrame(
            deaths, columns=["deaths", geo_loc_key]
        )
        self.df = reduce(
            lambda  left,right: pd.merge(
                left,right,on=[geo_loc_key], how='outer'
            ), [df_cases, df_recovered, df_deaths]
        )
        self.df.fillna(0, inplace=True)
        self.df["cases"] = self.df.cases.astype(int)
        self.df["recovered"] = self.df.recovered.astype(int)
        self.df["deaths"] = self.df.deaths.astype(int)

        # total = self.df[["cases", "recovered", "deaths"]].sum()
        # total["state"] = "sum"

        # self.df = self.df.append(
        #     pd.DataFrame(
        #         total
        #     ).T
        # )

        logger.info("cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        Aktuelle Situation Österreich 04.03.2020 / 17:45 Uhr
        Stand, 10.03.2020, 08:00 Uhr
        """
        doc = lxml.html.document_fromstring(self.req.text)
        el = doc.xpath('.//div[@class="infobox"]')
        if el:
            text = "".join(
                el[0].xpath('.//text()')
            )

        re_dt = re.compile(r'Bestätigte Fälle, Stand (\d{1,2}.\d{1,2}.\d{4}, \d{1,2}:\d{1,2}) Uhr:')
        text = html.unescape(text)
        dt_from_re = re_dt.findall(text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0].replace("/", "")
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)


if __name__ == "__main__":

    # column_converter = {
    #     "state": "nuts_2"
    # }
    # drop_rows = {
    #     "state": "sum"
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

    cov_at = SARSCOV2AT()
    cov_at.workflow()

    print(cov_at.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="AT",
        fill=False
    )
    da.workflow()

    print("End of Game")
