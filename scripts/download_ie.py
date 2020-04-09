import logging
import os
import re
import datetime
import json

import dateutil
import pandas as pd
import requests

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.es")

today_iso = datetime.date.today().isoformat()

# Download from Dashboard
REPORT_API = "https://services1.arcgis.com/eNO7HHeQ3rUcBllm/arcgis/rest/services/Covid19CountyStatisticsHPSCIrelandOpenData/FeatureServer/0/query?f=json&where=1%3D1&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&groupByFieldsForStatistics=CountyName&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22ConfirmedCovidCases%22%2C%22outStatisticFieldName%22%3A%22value%22%7D%5D&cacheHint=true"


TIMESERES_API = f"https://services1.arcgis.com/eNO7HHeQ3rUcBllm/arcgis/rest/services/CovidStatisticsProfileHPSCIrelandView/FeatureServer/0/query?f=json&where=Date%3Ctimestamp%20%27{today_iso}%2022%3A00%3A00%27&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=FID%2CConfirmedCovidCases%2CDate&orderByFields=Date%20asc&resultOffset=0&resultRecordCount=2000&cacheHint=true"

DAILY_FOLDER = os.path.join("dataset", "daily", "ie")
# For PDF Download
REPORT_URL = "https://www.hpsc.ie/a-z/respiratory/coronavirus/novelcoronavirus/casesinireland/epidemiologyofcovid-19inireland/"
PDF_BASE_URL = "https://www.hpsc.ie"
PDF_FOLDER = os.path.join("documents", "daily", "ie")

def download_pdf():
    try:
        req_page = requests.get(REPORT_URL,  timeout=20, verify=False)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    # /a-z/respiratory/coronavirus/novelcoronavirus/casesinireland/COVID-19 Epidemiology report for NPHET 23.03.2020_v1 website version.pdf
    re_pdf = re.compile(r"(/a-z/.+?\.pdf)")

    pdf_paths = list(
        set(re_pdf.findall(req_page.text))
    )

    if not pdf_paths:
        raise Exception("Could not find PDF links")

    pdf_paths = [PDF_BASE_URL+i for i in pdf_paths]
    for pdf_path in pdf_paths:
        pdf_name = pdf_path.split("/")[-1]
        pdf_path_get = requests.get(pdf_path, timeout=30, verify=False)
        with open(
            os.path.join(PDF_FOLDER, pdf_name),
            'wb'
        ) as f:
            f.write(pdf_path_get.content)


def get_most_recent_date():

    req = requests.get(TIMESERES_API)
    data = req.json()["features"]
    data = [i["attributes"]["Date"] for i in data]
    data.sort()

    ts = data[-1]
    ts = int(ts)/1000
    dt = datetime.datetime.fromtimestamp(ts)

    return dt

def cache_ages_gender(dt, dt_upper):
    # https://services1.arcgis.com/eNO7HHeQ3rUcBllm/arcgis/rest/services/CovidStatisticsProfileHPSCIrelandView/FeatureServer/0/query?f=json&where=StatisticsProfileDate%3E%3Dtimestamp%20%272020-04-05T02:00:00%2022%3A00%3A00%27%20AND%20StatisticsProfileDate%3C%3Dtimestamp%20%272020-04-06T02:00:00%2021%3A59%3A59%27&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22HospitalisedCovidCases%22%2C%22outStatisticFieldName%22%3A%22HospitalisedCovidCases%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22RequiringICUCovidCases%22%2C%22outStatisticFieldName%22%3A%22RequiringICUCovidCases%22%7D%5D&cacheHint=true

    TOTAL_STATISTICS_API = f"https://services1.arcgis.com/eNO7HHeQ3rUcBllm/arcgis/rest/services/CovidStatisticsProfileHPSCIrelandView/FeatureServer/0/query?f=json&where=StatisticsProfileDate%3E%3Dtimestamp%20%27{dt.isoformat()}%2022%3A00%3A00%27%20AND%20StatisticsProfileDate%3C%3Dtimestamp%20%27{dt_upper.isoformat()}%2021%3A59%3A59%27&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22HospitalisedCovidCases%22%2C%22outStatisticFieldName%22%3A%22HospitalisedCovidCases%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22RequiringICUCovidCases%22%2C%22outStatisticFieldName%22%3A%22RequiringICUCovidCases%22%7D%5D&cacheHint=true"
    AGE_STATISTICS_API = f"https://services1.arcgis.com/eNO7HHeQ3rUcBllm/arcgis/rest/services/CovidStatisticsProfileHPSCIrelandView/FeatureServer/0/query?f=json&where=StatisticsProfileDate%3E%3Dtimestamp%20%27{dt.isoformat()}%2022%3A00%3A00%27%20AND%20StatisticsProfileDate%3C%3Dtimestamp%20%27{dt_upper.isoformat()}%2021%3A59%3A59%27&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Aged1%22%2C%22outStatisticFieldName%22%3A%22Aged1%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Aged1to4%22%2C%22outStatisticFieldName%22%3A%22Aged1to4%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Aged5to14%22%2C%22outStatisticFieldName%22%3A%22Aged5to14%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Aged15to24%22%2C%22outStatisticFieldName%22%3A%22Aged15to24%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Aged25to34%22%2C%22outStatisticFieldName%22%3A%22Aged25to34%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Aged35to44%22%2C%22outStatisticFieldName%22%3A%22Aged35to44%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Aged45to54%22%2C%22outStatisticFieldName%22%3A%22Aged45to54%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Aged55to64%22%2C%22outStatisticFieldName%22%3A%22Aged55to64%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Aged65up%22%2C%22outStatisticFieldName%22%3A%22Aged65up%22%7D%5D&cacheHint=true"
    GENDER_STATISTICS_API = f"https://services1.arcgis.com/eNO7HHeQ3rUcBllm/arcgis/rest/services/CovidStatisticsProfileHPSCIrelandView/FeatureServer/0/query?f=json&where=StatisticsProfileDate%3E%3Dtimestamp%20%27{dt.isoformat()}%2022%3A00%3A00%27%20AND%20StatisticsProfileDate%3C%3Dtimestamp%20%27{dt_upper.isoformat()}%2021%3A59%3A59%27&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Male%22%2C%22outStatisticFieldName%22%3A%22Male%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Female%22%2C%22outStatisticFieldName%22%3A%22Female%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22Unknown%22%2C%22outStatisticFieldName%22%3A%22Unknown%22%7D%5D&cacheHint=true"
    TRANSMISSION_STATISTICS_API = f"https://services1.arcgis.com/eNO7HHeQ3rUcBllm/arcgis/rest/services/CovidStatisticsProfileHPSCIrelandView/FeatureServer/0/query?f=json&where=StatisticsProfileDate%3E%3Dtimestamp%20%27{dt.isoformat()}%2022%3A00%3A00%27%20AND%20StatisticsProfileDate%3C%3Dtimestamp%20%27{dt_upper.isoformat()}%2021%3A59%3A59%27&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=*&outStatistics=%5B%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22CommunityTransmission%22%2C%22outStatisticFieldName%22%3A%22CommunityTransmission%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22CloseContact%22%2C%22outStatisticFieldName%22%3A%22CloseContact%22%7D%2C%7B%22statisticType%22%3A%22sum%22%2C%22onStatisticField%22%3A%22TravelAbroad%22%2C%22outStatisticFieldName%22%3A%22TravelAbroad%22%7D%5D&cacheHint=true"

    req = requests.get(AGE_STATISTICS_API)
    data = req.json()["features"]
    data = data[0]
    data = data["attributes"]

    req_gender = requests.get(GENDER_STATISTICS_API)
    data_gender = req_gender.json()["features"]
    data_gender = data_gender[0]
    data_gender = data_gender["attributes"]

    req_trans = requests.get(TRANSMISSION_STATISTICS_API)
    data_trans = req_trans.json()["features"]
    data_trans = data_trans[0]
    data_trans = data_trans["attributes"]

    req_hosp = requests.get(TOTAL_STATISTICS_API)
    data_hosp = req_hosp.json()["features"]
    data_hosp = data_hosp[0]

    combined = {
        **{
            "datetime": dt.isoformat()
        },
        **data,
        **data_gender,
        **data_trans,
        **data_hosp
    }

    file_path = os.path.join(PDF_FOLDER, f'ie_ages_and_gender_{dt.strftime("%Y%m%d%H%M")}.json')
    with open(file_path, "w+") as fp:
        json.dump(combined, fp)


class SARSCOV2IE(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_API

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="IE", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        geo_loc_key = 'lau'

        data = self.req.json().get("features")
        data = [
            {
                geo_loc_key: i["attributes"]["CountyName"],
                "cases": i["attributes"]["value"]
            } for i in data
        ]

        self.df = pd.DataFrame(data)

        logger.info("cases:\n", self.df)


    def extract_datetime(self):
        """Get datetime of dataset
        """

        self.dt = get_most_recent_date()


    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)


if __name__ == "__main__":

    logger.info("Downloading PDF")
    download_pdf()

    logger.info("Download data from dashboard")
    current_dt = get_most_recent_date()

    cov_ie = SARSCOV2IE()
    cov_ie.workflow()

    print(cov_ie.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="IE",
        fill=False
    )
    da.workflow()


    logger.info("Cache other data")
    list_of_dates = [current_dt - datetime.timedelta(days=i) for i in range(5)]
    for i in list_of_dates:
        i = i.date()
        try:
            cache_ages_gender(
                i - datetime.timedelta(days=1),
                i
            )
            logger.info(
                f"Cached ages and gender for {i - datetime.timedelta(days=1)} to {i}"
            )
        except Exception as e:
            logger.error(
                f"Did not cache ages and gender for {i - datetime.timedelta(days=1)} to {i}"
            )

    print("End of Game")
