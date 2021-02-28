import datetime
from loguru import logger
import os
from functools import reduce

import click
import dateutil
from lxml import html
import pandas as pd
import requests

from utils import COVIDScrapper, DailyAggregator
from utils import get_response as _get_response


# REPORT_URL = "https://epidemio.wiv-isp.be/ID/Pages/2019-nCoV_epidemiological_situation.aspx"
REPORT_URL = "https://covid-19.sciensano.be/nl/covid-19-epidemiologische-situatie"
REPORT_XLSX = "https://epistat.sciensano.be/Data/COVID19BE.xlsx"
DATA_PAGE = "https://epistat.wiv-isp.be/Covid/"

PDF_BASE_URL = "https://epidemio.wiv-isp.be"
DOCS_DAILY_FOLDER = os.path.join("documents", "daily", "be")
DAILY_FOLDER = os.path.join("dataset", "daily", "be")

CURRENT_DT = datetime.date.today().isoformat()

def download_pdf():
    try:
        req_page = _get_response(REPORT_URL)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    # "Meest recent epidemiologische update"
    report_doc = html.document_fromstring(req_page.content.decode("utf-8"))
    pdf_el = report_doc.xpath('.//a[@title="Meest recente update.pdf"]/@href')
    pdfs = pdf_el

    if not pdfs:
        raise Exception("No link to pdf found!")

    try:
        os.makedirs(DOCS_DAILY_FOLDER)
    except FileExistsError as e:
        logger.info(f"{DOCS_DAILY_FOLDER} already exists, no need to create folder")
        pass

    for pdf in pdfs:
        pdf_url = pdf
        pdf_dt = datetime.date.today().isoformat()

        pdf_url_get = requests.get(pdf_url)
        pdf_name = pdf.split("/")[-1]

        with open(
            os.path.join(DOCS_DAILY_FOLDER, f"{pdf_name}"),
            'wb'
        ) as f:
            f.write(pdf_url_get.content)


def download_data():

    try:
        req_page = _get_response(DATA_PAGE)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    report_doc = html.document_fromstring(req_page.content.decode("utf-8"))
    xlsx_el = report_doc.xpath('.//a[contains(@href,".xlsx")]/@href')
    csv_el = report_doc.xpath('.//a[contains(@href,".csv")]/@href')
    links = csv_el + xlsx_el

    if not links:
        raise Exception("No link to pdf found!")

    current_dt = datetime.date.today().isoformat()

    for link in links:
        link_get = requests.get(link)
        file_name = link.split("/")[-1]

        with open(
            os.path.join(DOCS_DAILY_FOLDER, f"{file_name}"),
            'wb'
        ) as f:
            f.write(link_get.content)



class SARSCOV2BE(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None, history=None):
        self.date_index = -1

        if url is None:
            url = REPORT_XLSX

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        if history is None:
            history = False
        self.history = history

        self.geo_level = 'nuts_3'
        self.geo_level_code = 'nuts_3_code'

        COVIDScrapper.__init__(
            self, url, country="BE", daily_folder=daily_folder,
            cache_format='.xlsx'
        )

    def _cumulative_values(self, df, date):

        df_res = df.copy()

        df_res.rename(
            columns={
                'DATE': 'datetime'
            }, inplace=True
        )

        df_res = df_res.loc[df_res["datetime"] <= date]

        return df_res

    def extract_table(self):
        """Load data table from json
        """
        GEO_MISSING_FILLING = "MISSING"
        cols = {
            "DATE": "datetime",
            "REGION": "nuts_1", "PROVINCE": "nuts_2",
            "CASES": "cases",
            "TOTAL_IN": "hospitalized",
            "TOTAL_IN_ICU": "intensive_care",
            "DEATHS": "deaths"
        }

        df_cases = pd.read_excel(
            self.url, sheet_name="CASES_AGESEX"
        )
        df_cases.DATE = df_cases.DATE.apply(lambda x: dateutil.parser.parse(x) if isinstance(x,str) else x)
        df_cases.dropna(subset=['DATE'], inplace=True)
        # df_cases['DATE'] = df_cases.DATE.fillna(CURRENT_DT)
        df_cases.fillna(GEO_MISSING_FILLING, inplace=True)
        df_cases = df_cases[
            ['DATE', 'REGION', 'PROVINCE', 'CASES']
        ].groupby(['DATE', 'REGION', 'PROVINCE']).sum().reset_index()
        df_cases.rename(columns=cols, inplace=True)
        df_cases_cum = pd.DataFrame()
        for nuts_2 in df_cases.nuts_2.unique():
            df_cases_nuts_2 = df_cases.loc[df_cases.nuts_2 == nuts_2]
            df_cases_nuts_2.sort_values(by="datetime", inplace=True)
            df_cases_nuts_2 = pd.merge(
                df_cases_nuts_2[["datetime", "nuts_1", "nuts_2"]],
                pd.DataFrame(df_cases_nuts_2.cases.cumsum()),
                left_index=True, right_index=True, how="left"
            )
            df_cases_cum = pd.concat([df_cases_cum, df_cases_nuts_2])


        df_hospitalized = pd.read_excel(
            self.url, sheet_name="HOSP"
        )
        df_hospitalized = df_hospitalized[
            ['DATE', 'REGION', 'PROVINCE', 'TOTAL_IN', 'TOTAL_IN_ICU']
        ].groupby(['DATE', 'REGION', 'PROVINCE']).sum().reset_index()
        df_hospitalized.rename(columns=cols, inplace=True)


        df_deaths = pd.read_excel(
            self.url, sheet_name="MORT"
        )
        df_deaths = df_deaths.loc[df_deaths.AGEGROUP.isna()]
        df_deaths.DEATHS = df_deaths.DEATHS.apply(lambda x: float(x) if x else x)
        # df_deaths.DATE = df_deaths.DATE.apply(lambda x: dateutil.parser.parse(x) if x else None)
        df_deaths.DATE = pd.to_datetime(df_deaths.DATE, dayfirst=False)
        df_deaths.dropna(subset=['DATE'], inplace=True)
        df_deaths = df_deaths[
            ['DATE', 'REGION', 'DEATHS']
        ].groupby(['DATE', 'REGION']).sum().reset_index()
        df_deaths["PROVINCE"] = ""
        df_deaths.rename(columns=cols, inplace=True)
        df_deaths_cum = pd.DataFrame()
        for nuts_1 in df_deaths.nuts_1.unique():
            df_deaths_nuts_1 = df_deaths.loc[df_deaths.nuts_1 == nuts_1]
            df_deaths_nuts_1.sort_values(by="datetime", inplace=True)
            df_deaths_nuts_1 = pd.merge(
                df_deaths_nuts_1[["datetime", "nuts_1", "nuts_2"]],
                pd.DataFrame(df_deaths_nuts_1.deaths.cumsum()),
                left_index=True, right_index=True, how="left"
            )
            df_deaths_cum = pd.concat([df_deaths_cum, df_deaths_nuts_1])

        # df_tests = pd.read_excel(
        #     self.url, sheet_name="TESTS", dtype={"DATE": str}
        # )


        dfs = [df_cases_cum, df_hospitalized, df_deaths_cum]

        self.df = reduce(
            lambda left,right: pd.merge(
                left,right,on=['datetime', 'nuts_1', 'nuts_2'], how="outer"
            ), dfs
        )
        self.df.sort_values(by="datetime", inplace=True)
        self.df.datetime = self.df.datetime.apply(lambda x: x.date().isoformat())

        self.df['country'] = 'BE'

        self.dates = self.df['datetime'].unique().tolist()
        self.dates.sort(reverse=True)
        self.dates = [
            i for i in self.dates
            if (i and i != GEO_MISSING_FILLING)
        ]

        # Get full list of dates
        self.df_full = self.df.copy()
        self.df_full.sort_values(by=['datetime', 'cases'], inplace=True)
        if not self.history:
            date_idx = 0
            use_date = self.dates[date_idx]
            self.df = self._get_history(self.df_full, use_date)

    def _get_history(self, df, use_date):
        df_res =df.copy()

        df_res = df_res[df_res.datetime == use_date]
        self.dt = dateutil.parser.parse(use_date)
        df_res.sort_values(by='cases', inplace=True)

        return df_res

    def full_history(self):

        # post processing
        self.extract_table()
        for date in self.dates:#
            logger.info('Working on {date}')
            self.df = self._get_history(self.df_full, date)
            self.calculate_datetime()
            self.df.sort_values(by=['datetime', 'cases'], inplace=True)
            # save
            self.cache()


@click.command()
@click.option('-f', '--full', flag_value='full', default=False, help='Use to download and process cases for all dataes.')
def download(full):

    if full:
        scrapper = SARSCOV2BE(history=True)
        logger.info('Downloading cases for all dates ...')
        scrapper.full_history()

    else:
        scrapper = SARSCOV2BE()
        logger.info('Downloading cases for the last day only ...')
        scrapper.workflow()

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="BE",fill=False
    )
    da.workflow()



if __name__ == "__main__":

    download_pdf()

    download_data()

    download()

    print("End of Game")
