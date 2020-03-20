import json
import logging
import os
import io
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html
import lxml

from utils import _COLUMNS_ORDER, COVIDScrapper, DailyAggregator


logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.cz")

REPORT_URL = "https://onemocneni-aktualne.mzcr.cz/covid-19"
DAILY_FOLDER = os.path.join("dataset", "daily", "cz")
WEBPAGE_CACHE_FOLDER = os.path.join("documents", "daily", "cz")


class SARSCOV2CZ(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="CZ", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        doc = lxml.html.document_fromstring(self.req.content.decode("utf-8"))
        el = doc.xpath('.//div[@id="js-total-regions-data"]')
        if el:
            text = "".join(
                el[0].get('data-barchart')
            )

        data = json.loads(text)

        self.df = pd.DataFrame(data.get('values'))
        self.df.drop('color', axis=1, inplace=True)
        self.df.rename(
            columns = {
                "x": "authority",
                "y": "cases"
            },
            inplace=True
        )

        # add sum
        total = self.df.cases.sum()
        self.df = self.df.append(
            pd.DataFrame(
                [["sum", total]], columns=["authority", "cases"]
            )
        )

        logger.info("list of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """

        doc = lxml.html.document_fromstring(self.req.content.decode("utf-8"))
        el = doc.xpath(
            './/div[@class="column small-12 medium-12 large-12 mb-15"]/div[@class="legend legend--inverse mt-15"]'
        )
        if el:
            text = "\n".join(
                el[0].xpath('.//text()')
            )
        # Poslední aktualizace pozitivních nálezů byla provedena ke dni: 20.\xa03.\xa02020\xa0v\xa017.55h\n
        re_dt = re.compile(r': (.*)\xa0v\xa0(.*)h\n')
        dt_from_re = re_dt.findall(text)

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        def parse_dt(inp):
            dt_from_re_date = inp[0].replace('\xa0', ' ')
            dt_from_re_time = inp[1].replace('\xa0', ' ').replace('.', ':')
            res = " ".join([dt_from_re_date, dt_from_re_time])
            return res

        dt_from_re = parse_dt(dt_from_re[0])

        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)

        try:
            os.makedirs(WEBPAGE_CACHE_FOLDER)
        except FileExistsError as e:
            logger.info(f"{WEBPAGE_CACHE_FOLDER} already exists, no need to create folder")
            pass
        with open(
        os.path.join(WEBPAGE_CACHE_FOLDER, f"{self.dt.date().isoformat()}.html"),
            'wb'
        ) as f:
            f.write(self.req.content)


if __name__ == "__main__":
    cov_cz = SARSCOV2CZ()
    cov_cz.workflow()

    print(cov_cz.df)
    if cov_cz.df.empty:
        raise Exception("Empty dataframe for CZ data")

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="CZ"
    )
    da.workflow()

    print("End of Game")
