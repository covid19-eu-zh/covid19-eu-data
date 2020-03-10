import logging
import os
import re

import dateutil
import pandas as pd
import requests

from utils import _COLUMNS_ORDER, COVIDScrapper

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.fr")

FR_REPORT_URL = ("https://www.santepubliquefrance.fr/maladies-et-traumatismes/"
"maladies-et-infections-respiratoires/infection-a-coronavirus/articles/"
"infection-au-nouveau-coronavirus-sars-cov-2-covid-19-france-et-monde")
PDF_BASE_URL = "https://www.santepubliquefrance.fr"
DAILY_FOLDER = os.path.join("documents", "daily", "fr")


if __name__ == "__main__":

    try:
        req_page = requests.get(FR_REPORT_URL)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    re_pdf = re.compile(
        r'<h4><a href="?(/content/download/\d*?/\d*?)">Point épidémiologique du (07/03/2020, 15h)</a></h4>'
    )

    re_pdf_res = re_pdf.findall(req_page.text)

    if not re_pdf_res:
        raise Exception("No link to pdf found!")

    pdf_path, dt_str = re_pdf_res[0]
    pdf_url = PDF_BASE_URL + pdf_path
    pdf_dt = dateutil.parser.parse(dt_str, dayfirst=True).isoformat()
    pdf_dt = pdf_dt.replace(":","-")

    pdf_url_get = requests.get(pdf_url)

    with open(
        os.path.join(DAILY_FOLDER, f"{pdf_dt}.pdf"),
        'wb'
    ) as f:
        f.write(pdf_url_get.content)


    print("End of Game")
