import logging
import os
import re

import dateutil
import pandas as pd
import requests

from utils import _COLUMNS_ORDER, COVIDScrapper, get_response

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.fr")

FR_REPORT_URL = "https://www.santepubliquefrance.fr/maladies-et-traumatismes/maladies-et-infections-respiratoires/infection-a-coronavirus/articles/infection-au-nouveau-coronavirus-sars-cov-2-covid-19-france-et-monde"
PDF_BASE_URL = "https://www.santepubliquefrance.fr"
DAILY_FOLDER = os.path.join("documents", "daily", "fr")



if __name__ == "__main__":

    try:
        req_page = requests.get(FR_REPORT_URL, verify=False)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    # <a href="/maladies-et-traumatismes/maladies-et-infections-respiratoires/infection-a-coronavirus/documents/bulletin-national/covid-19-point-epidemiologique-du-24-mars-2020"></a>
    re_pdf = re.compile(
        r'<a href="(/maladies-et-traumatismes/maladies-et-infections-respiratoires/infection-a-coronavirus/documents/bulletin-national/.*?)"></a>'
    )

    re_pdf_page_res = re_pdf.findall(req_page.text)

    if not re_pdf_page_res:
        raise Exception("No link to pdf page found!")

    pdf_page = PDF_BASE_URL + re_pdf_page_res[0]

    # Download pdf page
    try:
        req_pdf_page = requests.get(pdf_page, verify=False)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")
    # href="/content/download/239617/2544833"
    #                                       class="button button--pdf"
    #                                       title="COVID19-PE_20200324"
    re_pdf_link = re.compile(
        r'href="(/content/download/.*?)"(?:.|\n)+?title="(.*?)"'
    )
    pdf_link_and_name = re_pdf_link.findall(req_pdf_page.content.decode("utf-8"))

    if not pdf_link_and_name:
        raise Exception("No link to pdf found!")

    pdf_link, pdf_name = pdf_link_and_name[0]

    pdf_url = PDF_BASE_URL + pdf_link

    pdf_url_get = requests.get(pdf_url, verify=False)

    with open(
        os.path.join(DAILY_FOLDER, f"{pdf_name}.pdf"),
        'wb'
    ) as f:
        logger.info(f'Writing to {os.path.join(DAILY_FOLDER, f"{pdf_name}.pdf")}')
        f.write(pdf_url_get.content)


    print("End of Game")
