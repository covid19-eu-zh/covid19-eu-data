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
                   DailyTransformation, retrieve_files, get_response)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.nl")

REPORT_URL = "https://www.rivm.nl/coronavirus-kaart-van-nederland-per-gemeente"
COUNTRY_REPORT_URL = "https://www.rivm.nl/nieuws/actuele-informatie-over-coronavirus"
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
            io.StringIO(text), sep=";", header=None
        )
        # self.df = self.df[[0, 1, 2, 3, 4]]
        self.df.columns = self.df.iloc[0]
        self.df = self.df.iloc[1:]
        # cols = text.split("\n")[1].split(";")
        # self.df.columns = cols
        df_other = self.df.loc[self.df.Gemnr == -1]
        df_other.Gemeente = "Other"

        self.df['Gemnr'] = self.df.Gemnr.astype(int)
        self.df = self.df.loc[
            self.df.Gemnr >= 0
        ]
        self.df = pd.concat([self.df, df_other])

        original_cols = ["Gemeente", "Meldingen", "Zkh opname", "BevAant", "Meldingen per 100.000", "Zkh opname per 100.000"]
        self.df = self.df[original_cols]
        self.df.fillna(0, inplace=True)
        self.df["Meldingen"] = self.df.Meldingen.astype(int)
        self.df["Zkh opname"] = self.df["Zkh opname"].astype(int)

        self.df.rename(
            columns={
                "Gemeente": "lau",
                "BevAant": "population",
                "Meldingen": "cases",
                "Zkh opname": "hospitalized",
                "Meldingen per 100.000": "cases/100k pop.",
                "Zkh opname per 100.000": "hospitalized/100k pop."
            },
            inplace=True
        )

        self.df = pd.concat(
            [
                self.df,
                self._extract_total()
            ]
        )
        # add sum
        # total = self.df.Aantal.sum()
        # total_pop = self.df["BevAant"].sum()
        # self.df = self.df.append(
        #     pd.DataFrame(
        #         [["sum", total, total_pop, f"{total/total_pop:0.2f}"]], columns=original_cols
        #     )
        # )

        logger.info("list of cases:\n", self.df)

    def _extract_total(self):
        """
        COUNTRY_REPORT_URL
        """
        # # Totaal aantal testen positief in Nederland: 7431
        # re_total = re.compile(r"Totaal aantal testen positief in Nederland: (\d+)")
        # total = re_total.findall(self.req.content.decode("utf-8"))
        # if not total:
        #     raise Exception("Could not find total cases")

        #  17.851* (+1.224)
        re_count = re.compile(r"(.*)\(.*\)")
        df = pd.read_html(REPORT_URL)[0]
        df = df.T

        # values = el[0].xpath('.//span[@class="h3"]/text()')
        # values = [
        #     int(i.replace("*","").replace('.','').replace(',','.'))
        #     for i in values
        # ]
        headers = ["cases", "hospitalized", "deaths"]
        df.columns = headers
        df = df.iloc[1:2]
        for col in df.columns:
            df[col] = df[col].apply(
                lambda x: int(
                    x.strip().replace("*","").replace('.','').replace(',','.')
                )
            )

        df.rename(
            columns={
                "Aantal": "cases"
            },
            inplace=True
        )

        # Het totaal aantal gemelde patiënten: 6412 (+852)
        # re_total_cases = re.compile(
        #     r"Het totaal aantal gemelde patiënten: (\d+)"
        # )
        # re_total_deaths = re.compile(r"Het totaal aantal gemelde overleden patiënten: (\d+)")
        # re_total_hospitalized = re.compile(r"Het totaal aantal gemelde patiënten opgenomen \(geweest\) in het ziekenhuis: (\d+)")

        # total_cases = re_total_cases.findall(req.content.decode("utf-8"))[0]
        # total_deaths = re_total_deaths.findall(req.content.decode("utf-8"))[0]
        # total_hospitalized = re_total_hospitalized.findall(req.content.decode("utf-8"))[0]

        # ["Gemeente", "Aantal", "BevAant", "Aantal per 100.000 inwoners"]
        return df

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
        # Wijzigingsdatum 31-03-2020 | 15:36
        # re_dt = re.compile(r"<p>aantal per (.*)uur</p>")
        re_dt = re.compile(r"Wijzigingsdatum (\d+-\d+-\d+ \| \d+:\d+)")
        dt_from_re = re_dt.findall(self.req.content.decode("utf-8"))

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0].replace("\xa0", " ").replace('|', '')
        for key in DUTCH_MONTHS_TO_EN:
            if key in dt_from_re:
                dt_from_re = dt_from_re.replace(key, DUTCH_MONTHS_TO_EN[key])
                break
        dt_from_re = dateutil.parser.parse(dt_from_re.replace(".", ":"), dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df = self.df[["country", "lau", "cases", "population", "hospitalized", "deaths", "datetime"]]

        self.df.sort_values(by="hospitalized", inplace=True)


if __name__ == "__main__":
    # column_converter = {
    #     "city": "lau"
    # }
    # drop_rows = {
    #     "city": "sum"
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

    cov_nl = SARSCOV2NL()
    cov_nl.workflow()

    print(cov_nl.df)
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

    print("End of Game")
