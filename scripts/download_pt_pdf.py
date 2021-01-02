import logging
import os
import re

import dateutil
import pandas as pd
import requests

from utils import _COLUMNS_ORDER, COVIDScrapper

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.es")

REPORT_URL = "https://covid19.min-saude.pt/relatorio-de-situacao/"
DAILY_FOLDER = os.path.join("documents", "daily", "pt")


if __name__ == "__main__":

    try:
        req_page = requests.get(REPORT_URL,  timeout=20, verify=False)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    # https://covid19.min-saude.pt/wp-content/uploads/2020/03/22_DGS_boletim_20200324_3.pdf
    re_pdf = re.compile(r"(https://covid19.min-saude.pt/wp-content/.+?\.pdf)")

    pdf_paths = list(
        set(re_pdf.findall(req_page.text))
    )

    if not pdf_paths:
        raise Exception("Could not find PDF links")

    for pdf_path in pdf_paths:
        pdf_name = pdf_path.split("/")[-1]
        pdf_path_get = requests.get(pdf_path, timeout=30, verify=False)
        with open(
            os.path.join(DAILY_FOLDER, pdf_name),
            'wb'
        ) as f:
            f.write(pdf_path_get.content)


    print("End of Game")
