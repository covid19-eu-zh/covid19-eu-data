import click
import logging
import os

import dateutil
from io import StringIO
import pandas as pd

from utils import COVIDScrapper, DailyAggregator

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.ch")

URL = "https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/covid19_cases_switzerland.csv"

DAILY_FOLDER = os.path.join("dataset", "daily", "ch")


class SARSCOV2CH(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        self.date_index = -1

        if url is None:
            url = URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="CH", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from json
        """

        self.df = pd.read_csv(StringIO(self.req.text))
        self.df = self.df.T

        # the first row of transposed DF is data
        self.dates = self.df[self.df.index == 'Date'].values[0]
        self.df = self.df[self.df.index != 'Date']
        self.dt = dateutil.parser.parse(self.dates[self.date_index])

        if self.date_index == -1:
            self.date_index = len(self.dates) - 1

        self.df = self.df[[self.date_index]]
        self.df.rename(columns={self.df.columns[0]: 'cases'}, inplace=True)
        self.df['nuts_2'] = self.df.index

        self.df['cases'] = self.df.cases.apply(lambda x: int(x) if not pd.isnull(x) else 0)
        self.df.sort_values(by='cases', inplace=True)
        self.df.drop(
            self.df.loc[
                self.df['nuts_2'] == 'CH'
            ].index,
            inplace=True
        )


@click.command()
@click.option('-f', '--full', flag_value='full', default=False, help='Use to download and process cases for all dataes.')
def download(full):
    scrapper = SARSCOV2CH()

    if full:
        logger.info('Downloading cases for all dates ...')
        scrapper.extract_table()
        for i in range(len(scrapper.dates)):
            scrapper.date_index = i  # small hack to avoid refactoring
            scrapper.workflow()
    else:
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
