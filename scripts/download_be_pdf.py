import logging
import os
import re

import datetime
import dateutil
import pandas as pd
import requests

from utils import get_response as _get_response


logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.be")

REPORT_URL = "https://epidemio.wiv-isp.be/ID/Pages/2019-nCoV_epidemiological_situation.aspx"

PDF_BASE_URL = "https://epidemio.wiv-isp.be"
DAILY_FOLDER = os.path.join("documents", "daily", "be")


if __name__ == "__main__":

    try:
        req_page = _get_response(REPORT_URL)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    re_pdf = re.compile(r'href="(.*\.pdf)"')
    pdfs = list(set(
        re_pdf.findall(req_page.content.decode("utf-8"))
    ))

    if not pdfs:
        raise Exception("No link to pdf found!")

    try:
        os.makedirs(DAILY_FOLDER)
    except FileExistsError as e:
        logger.info(f"{DAILY_FOLDER} already exists, no need to create folder")
        pass

    for pdf in pdfs:
        pdf_url = PDF_BASE_URL + pdf
        pdf_dt = datetime.date.today().isoformat()

        pdf_url_get = requests.get(pdf_url)
        pdf_name = pdf.split("/")[-1]

        with open(
            os.path.join(DAILY_FOLDER, f"{pdf_dt}__{pdf_name}"),
            'wb'
        ) as f:
            f.write(pdf_url_get.content)


    print("End of Game")
