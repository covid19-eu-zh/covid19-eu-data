import io
import json
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
logger = logging.getLogger("covid-eu-data.download.cz")

REPORT_URL = "https://onemocneni-aktualne.mzcr.cz/covid-19"
TEST_URL = "https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19/testy.csv"
CASES_URL = "https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19/nakaza.csv"
CASES_DETAILS_URL = "https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19/osoby.csv"

DAILY_FOLDER = os.path.join("dataset", "daily", "cz")
WEBPAGE_CACHE_FOLDER = os.path.join("cache", "daily", "cz")
API_CACHE_FOLDER = os.path.join("cache", "daily", "cz", "api")


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
        el = doc.xpath('.//div[@id="js-total-isin-regions-data"]')
        if el:
            text = "".join(
                el[0].get('data-barchart')
            )

        data = json.loads(text)

        self.df = pd.DataFrame(data.get('values'))
        self.df.drop('color', axis=1, inplace=True)
        self.df.rename(
            columns = {
                "x": "nuts_3",
                "y": "cases"
            },
            inplace=True
        )

        # add sum
        # total = self.df.cases.sum()
        # self.df = self.df.append(
        #     pd.DataFrame(
        #         [["sum", total]], columns=["nuts_3", "cases"]
        #     )
        # )

        logger.info("list of cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        """

        doc = lxml.html.document_fromstring(self.req.content.decode("utf-8"))
        el = doc.xpath(
            './/div[@class="legend legend--inverse mt-15"]/text()'
        )
        if el:
            text = "\n".join(
                el
            )
        # Poslední aktualizace pozitivních nálezů byla provedena ke dni: 20.\xa03.\xa02020\xa0v\xa017.55h\n
        # Poslední aktualizace pozitivních nálezů byla provedena ke dni: 29. 3. 2020 v 18.25 h

        re_dt = re.compile(r'provedena ke dni: (.*)[^0-9]*v[^0-9]*(\d+.\d+).*h')
        dt_from_re = re_dt.findall(self.req.content.decode("utf-8").replace("&nbsp;",""))

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



def cache_content(url, save_as):
    save_as_folder = "/".join(save_as.split("/")[:-1])
    if not os.path.exists(save_as_folder):
        os.makedirs(save_as_folder)

    req = get_response(url)
    with open(
            save_as,
            'wb'
        ) as f:
            f.write(req.content)



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

    # cache data files
    # https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19
    DATA_INDEX_URL = "https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19"
    DATA_API_BASE_URL = "https://onemocneni-aktualne.mzcr.cz"
    req = get_response(DATA_INDEX_URL)
    content = req.content.decode(req.apparent_encoding)
    doc = lxml.html.document_fromstring(content)
    links = doc.xpath('//a/@href')
    links = [i for i in links if (i.endswith(".csv") or i.endswith(".json"))]

    for link in links:
        path = os.path.join(API_CACHE_FOLDER, link[1:])
        link = DATA_API_BASE_URL + link
        cache_content(url=link, save_as=path)

    print("End of Game")
