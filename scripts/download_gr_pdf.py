import logging
import os
import re

import dateutil
import pandas as pd
import requests

from utils import _COLUMNS_ORDER, COVIDScrapper

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.es")

REPORT_URL = "https://eody.gov.gr/neos-koronaios-covid-19/"
PDF_BASE_URL = "https://www.hpsc.ie"
DAILY_FOLDER = os.path.join("documents", "daily", "gr")


if __name__ == "__main__":

    try:
        req_page = requests.get(REPORT_URL,  timeout=20, verify=False)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    # https://eody.gov.gr/covid-gr-daily-report-20200324/
    # https://eody.gov.gr/wp-content/uploads/2020/04/covid-gr-daily-report-20200410-1.pdf
    # re_pdf = re.compile(r'(https://eody.gov.gr/wp-content/uploads/\d+/\d+/covid-gr-daily-report-.*?)"')
    re_pdf = re.compile(r'(https://eody.gov.gr/.*?covid-gr-daily-report-.*?)"')

    pdf_paths = list(
        set(re_pdf.findall(req_page.text))
    )

    if not pdf_paths:
        raise Exception("Could not find PDF links")

    for pdf_path in pdf_paths:
        pdf_name = pdf_path.split("/")
        pdf_name = [i for i in pdf_name if i][-1]
        pdf_name = f"{pdf_name}.pdf"
        pdf_path_get = requests.get(pdf_path, timeout=30, verify=False)
        with open(
            os.path.join(DAILY_FOLDER, pdf_name),
            'wb'
        ) as f:
            f.write(pdf_path_get.content)


    print("End of Game")
