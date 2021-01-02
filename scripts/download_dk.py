import logging
import os
import re

import datetime
import dateutil
import pandas as pd
import requests
import zipfile

from utils import get_response as _get_response


logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.dk")

# REPORT_URL = "https://www.ssi.dk/aktuelt/sygdomsudbrud/coronavirus/covid-19-i-danmark-epidemiologisk-overvaagningsrapport"
# REPORT_URL = "https://www.ssi.dk/sygdomme-beredskab-og-forskning/sygdomsovervaagning/c/covid19-overvaagning"
DATA_PAGE_URL = "https://covid19.ssi.dk/overvagningsdata/download-fil-med-overvaagningdata"

DAILY_FOLDER = os.path.join("documents", "daily", "dk")
CACHE_DAILY_FOLDER = os.path.join("cache", "daily", "dk")
os.makedirs(CACHE_DAILY_FOLDER, exist_ok=True)

def download_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)

if __name__ == "__main__":

    try:
        req_page = _get_response(DATA_PAGE_URL)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    # https://files.ssi.dk/covid19/overvagning/data/data-epidemiologiske-rapport-12112020-ql82
    re_zip = re.compile(r'href="(https://files.ssi.dk/covid19/overvagning/data/data-epidemiologiske-rapport.*?)"')

    zip_paths = list(set(
        re_zip.findall(req_page.content.decode("utf-8"))
    ))

    if not zip_paths:
        raise Exception("No link to pdf found!")

    re_date = re.compile(r'rapport-(.*?)-')

    try:
        os.makedirs(DAILY_FOLDER)
    except FileExistsError as e:
        logger.info(f"{DAILY_FOLDER} already exists, no need to create folder")
        pass

    uri_resources = [{"uri":i, "date": datetime.datetime. strptime(re_date.findall(i)[0], "%d%m%Y")} for i in zip_paths]

    recent_uri_resources = sorted(uri_resources, key=lambda k: k['date'])[-1]
    zip_filename = recent_uri_resources["uri"].split("/")[-1] + ".zip"
    zip_local_path = os.path.join(CACHE_DAILY_FOLDER, zip_filename)

    download_url(
        recent_uri_resources["uri"],
        zip_local_path
    )

    with zipfile.ZipFile(zip_local_path, 'r') as zip_ref:
        zip_ref.extractall(DAILY_FOLDER)

    print("End of Game")
