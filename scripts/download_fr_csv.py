import json
import logging
import os
import re

import dateutil
import pandas as pd
import requests
from bs4 import BeautifulSoup

from utils import _COLUMNS_ORDER, COVIDScrapper, get_response

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.fr")

FR_REPORT_URL = "https://www.data.gouv.fr/fr/datasets/indicateurs-de-lactivite-epidemique-taux-dincidence-de-lepidemie-de-covid-19-par-metropole/#community-resources"
FR_DATA_BASE_URL = "https://www.data.gouv.fr/fr/datasets/r/"
DAILY_FOLDER = os.path.join("documents", "daily", "fr")


def get_ld_json(html_text):
    parser = "html.parser"
    soup = BeautifulSoup(html_text, parser)
    return json.loads("".join(soup.find("script", {"type":"application/ld+json"}).contents))

def get_csv_urls(jsonld):
    datasets = jsonld["distribution"]

    covid_datasets = [
        i for i in datasets
        if i["name"] in [
            "metadonnees-sg-metro-opendata.csv",
            "metropole-epci.csv",
            "region-departement-epci.csv",
            "sg-metro-opendata.csv"
        ]
    ]


    return covid_datasets


if __name__ == "__main__":

    try:
        req_page = requests.get(FR_REPORT_URL, verify=False)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    # re_csv = re.compile(
    #     r'<article id="resource-(.*?)" class="card resource-card'
    # )

    # re_csv_page_res = re_csv.findall(req_page.text)
    # csv_name = re_csv_page_res[0]

    # if not re_csv_page_res:
    #     raise Exception("No link to pdf page found!")
    # csv_file = FR_DATA_BASE_URL + csv_name

    jsonld = get_ld_json(req_page.text)

    csv_file = get_csv_urls(jsonld)

    try:
        req_pdf_page = requests.get(csv_file, verify=False)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")


    csv_url_get = requests.get(csv_file, verify=False)

    with open(
        os.path.join(DAILY_FOLDER, f"sg-metro-opendata.csv"),
        'wb'
    ) as f:
        logger.info(f'Writing to {os.path.join(DAILY_FOLDER, f"sg-metro-opendata.csv")}')
        f.write(csv_url_get.content)


    print("End of Game")
