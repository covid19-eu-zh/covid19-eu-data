import logging
import os
import re

import dateutil
import pandas as pd
import requests

from utils import _COLUMNS_ORDER, COVIDScrapper

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.es")

ES_REPORT_URL = "http://www.mscbs.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov-China/situacionActual.htm"
PDF_BASE_URL = "http://www.mscbs.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov-China/"
DAILY_FOLDER = os.path.join("documents", "daily", "es")


if __name__ == "__main__":

    try:
        req_page = requests.get(ES_REPORT_URL,  timeout=20, verify=False)
    except Exception as e:
        raise Exception(f"Could not get web page content: {e}")

    re_pdf = re.compile(r"(documentos/.+?\.pdf)")

    pdf_paths = list(
        set(re_pdf.findall(req_page.text))
    )

    if not pdf_paths:
        raise Exception("Could not find PDF links")

    pdf_paths = [
        PDF_BASE_URL+i for i in pdf_paths
        if "Informacion_inicial_alerta" not in i
    ]

    for pdf_path in pdf_paths:
        pdf_name = pdf_path.split("/")[-1]
        pdf_path_get = requests.get(pdf_path, timeout=30, verify=False)
        with open(
            os.path.join(DAILY_FOLDER, pdf_name),
            'wb'
        ) as f:
            f.write(pdf_path_get.content)


    print("End of Game")
