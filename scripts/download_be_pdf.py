import logging
import os
import re

import datetime
import dateutil
import pandas as pd
import requests
import lxml

from utils import get_response as _get_response


logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.be")

# REPORT_URL = "https://epidemio.wiv-isp.be/ID/Pages/2019-nCoV_epidemiological_situation.aspx"
REPORT_URL = "https://covid-19.sciensano.be/nl/covid-19-epidemiologische-situatie"
REPORT_XLSX = "https://epistat.sciensano.be/Data/COVID19BE.xlsx"
DATA_PAGE = "https://epistat.wiv-isp.be/Covid/"

PDF_BASE_URL = "https://epidemio.wiv-isp.be"
DAILY_FOLDER = os.path.join("documents", "daily", "be")


def download_pdf():
    try:
        req_page = _get_response(REPORT_URL)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    # "Meest recent epidemiologische update"
    report_doc = lxml.html.document_fromstring(req_page.content.decode("utf-8"))
    pdf_el = report_doc.xpath('.//a[@title="Meest recente update.pdf"]/@href')
    pdfs = pdf_el

    if not pdfs:
        raise Exception("No link to pdf found!")

    try:
        os.makedirs(DAILY_FOLDER)
    except FileExistsError as e:
        logger.info(f"{DAILY_FOLDER} already exists, no need to create folder")
        pass

    for pdf in pdfs:
        pdf_url = pdf
        pdf_dt = datetime.date.today().isoformat()

        pdf_url_get = requests.get(pdf_url)
        pdf_name = pdf.split("/")[-1]

        with open(
            os.path.join(DAILY_FOLDER, f"{pdf_dt}__{pdf_name}"),
            'wb'
        ) as f:
            f.write(pdf_url_get.content)


def download_data():

    try:
        req_page = _get_response(DATA_PAGE)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    report_doc = lxml.html.document_fromstring(req_page.content.decode("utf-8"))
    xlsx_el = report_doc.xpath('.//a[contains(@href,".xlsx")]/@href')
    csv_el = report_doc.xpath('.//a[contains(@href,".csv")]/@href')
    links = csv_el + xlsx_el

    if not links:
        raise Exception("No link to pdf found!")

    current_dt = datetime.date.today().isoformat()

    for link in links:
        link_get = requests.get(link)
        file_name = link.split("/")[-1]

        with open(
            os.path.join(DAILY_FOLDER, f"{file_name}"),
            'wb'
        ) as f:
            f.write(link_get.content)



if __name__ == "__main__":

    download_pdf()

    download_data()


    print("End of Game")
