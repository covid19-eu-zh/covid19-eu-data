import click
import logging
import os

from functools import reduce

import dateutil
from io import StringIO
import pandas as pd

from utils import COVIDScrapper, DailyAggregator

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.ch")

URL = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/covid19_cases_switzerland.csv"
XLSX_URL = "https://github.com/daenuprobst/covid19-cases-switzerland/raw/master/covid_19_data_switzerland.xlsx"

DAILY_FOLDER = os.path.join("dataset", "daily", "ch")

CH_CANTONS = {'nuts_3': {'AG': 'Aargau',
  'AI': 'Appenzell Innerrhoden',
  'AR': 'Appenzell Ausserrhoden',
  'BE': 'Berne',
  'BL': 'Basel-Landschaft',
  'BS': 'Basel-Stadt',
  'FR': 'Fribourg',
  'GE': 'Geneva',
  'GL': 'Glarus',
  'GR': 'Grisons',
  'JU': 'Jura',
  'LU': 'Lucerne',
  'NE': 'Neuchâtel',
  'NW': 'Nidwalden',
  'OW': 'Obwalden',
  'SG': 'St. Gallen',
  'SH': 'Schaffhausen',
  'SO': 'Solothurn',
  'SZ': 'Schwyz',
  'TG': 'Thurgau',
  'TI': 'Ticino',
  'UR': 'Uri',
  'VD': 'Vaud',
  'VS': 'Valais',
  'ZG': 'Zug',
  'ZH': 'Zürich'}}

class SARSCOV2CH(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None, history=None):
        self.date_index = -1

        if url is None:
            url = XLSX_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        if history is None:
            history = False
        self.history = history

        self.geo_level = 'nuts_3'
        self.geo_level_code = 'nuts_3_code'

        COVIDScrapper.__init__(
            self, url, country="CH", daily_folder=daily_folder,
            cache_format='.xlsx'
        )

    def _melt_columns(self, df, name):

        df_res = pd.melt(
            df, id_vars=['Date'],
            value_vars=df.columns.to_list().remove('Date')
        )
        df_res.rename(
            columns={
                'Date': 'datetime',
                'variable': self.geo_level_code,
                'value': name
            }, inplace=True
        )

        return df_res

    def extract_table(self):
        """Load data table from json
        """
        df_cases = pd.read_excel(
            self.url,sheet_name="Cases"
        )
        df_cases = self._melt_columns(df_cases, 'cases')
        df_tested = pd.read_excel(
            self.url,sheet_name="Tested"
        )
        df_tested = self._melt_columns(df_tested, 'tests')
        df_deaths = pd.read_excel(
            self.url,sheet_name="Fatalities"
        )
        df_deaths = self._melt_columns(df_deaths, 'deaths')
        df_hospitalized = pd.read_excel(
            self.url,sheet_name="Hospitalized"
        )
        df_hospitalized = self._melt_columns(df_hospitalized, 'hospitalized')

        df_intensive_care = pd.read_excel(self.url, sheet_name='ICU')
        df_intensive_care = self._melt_columns(df_intensive_care, 'intensive_care')

        dfs = [df_cases, df_tested, df_deaths, df_hospitalized, df_intensive_care]

        self.df = reduce(
            lambda left,right: pd.merge(left,right,on=['datetime', self.geo_level_code]), dfs
        )

        # remove CH as nuts_2
        self.df.replace('CH', '', inplace=True)
        self.df['country'] = 'CH'

        df_nuts_map = pd.DataFrame(CH_CANTONS).reset_index().rename(
            columns={'index': 'nuts_3_code'}
        )
        self.df = pd.merge(
            self.df, df_nuts_map, how='left',
            left_on=self.geo_level_code, right_on=self.geo_level_code
        )

        self.dates = self.df['datetime'].unique().tolist()
        self.dates.sort(reverse=True)

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
        scrapper = SARSCOV2CH(history=True)
        logger.info('Downloading cases for all dates ...')
        scrapper.full_history()

    else:
        scrapper = SARSCOV2CH()
        logger.info('Downloading cases for the last day only ...')
        scrapper.workflow()

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="CH"
    )
    da.workflow()


if __name__ == '__main__':
    download()
