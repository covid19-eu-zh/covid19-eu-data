import logging
import os
import re

import dateutil
import pandas as pd
import requests
from lxml import etree, html

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   DailyTransformation, retrieve_files)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.fr")

REPORT_URL = "https://www.santepubliquefrance.fr/maladies-et-traumatismes/maladies-et-infections-respiratoires/infection-a-coronavirus/articles/infection-au-nouveau-coronavirus-sars-cov-2-covid-19-france-et-monde"
DAILY_FOLDER = os.path.join("dataset", "daily", "fr")

class SARSCOV2FR(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="FR", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """
        req_dfs = pd.read_html(self.req.content, flavor='lxml')

        if not req_dfs:
            raise Exception("Could not find data table in webpage")

        self.df = req_dfs[0][["Région de notification","Cas confirmés"]]

        self.df['Cas confirmés'] = self.df['Cas confirmés'].apply(
            lambda x: int(float(
                x.replace("*","").replace('.','').replace(',','.').replace(' ','').strip()
            ))
        ).astype(int)

        # total = self.df.loc[
        #     (
        #         self.df["Région de notification"] == "Total Outre Mer"
        #     ) | (
        #         self.df["Région de notification"] == "Total Métropole"
        #     )
        # ]["Cas confirmés"].sum()

        # self.df = self.df.append(
        #     pd.DataFrame(
        #         [["sum", total]], columns=[
        #             "Région de notification", "Cas confirmés"
        #         ]
        #     )
        # )

        logger.info("records cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        Nombre de cas rapportés par région au 10/03/2020 à 15h (données Santé publique France)
        """
        re_dt = re.compile(r'au (\d{1,2}/\d{1,2}/\d{4}).*(\d{1,2}h) \(')
        dt_from_re = re_dt.findall(self.req.content.decode(self.req.apparent_encoding))

        if not dt_from_re:
            raise Exception("Did not find datetime from webpage")

        dt_from_re = dt_from_re[0]
        dt_from_re = " ".join(dt_from_re)
        dt_from_re = dateutil.parser.parse(dt_from_re, dayfirst=True)
        self.dt = dt_from_re

    def post_processing(self):

        self.df.rename(
            columns={
                "Région de notification": "nuts_2",
                "Cas confirmés": "cases"
            },
            inplace=True
        )

        self.df.sort_values(by="cases", inplace=True)
        self.df.replace("Total Outre Mer", "Oversea", inplace=True)
        self.df.replace("Total Métropole", "Metropolis", inplace=True)


if __name__ == "__main__":

    # column_converter = {
    #     "authority": "nuts_2"
    # }
    # drop_rows = {
    #     "authority": "sum"
    # }

    # daily_files = retrieve_files(DAILY_FOLDER)
    # daily_files.sort()

    # for file in daily_files:
    #     file_path = os.path.join(DAILY_FOLDER, file)
    #     file_transformation = DailyTransformation(
    #         file_path=file_path,
    #         column_converter=column_converter,
    #         drop_rows=drop_rows
    #     )
    #     file_transformation.workflow()

    # cov_fr = SARSCOV2FR()
    # cov_fr.workflow()

    print(cov_fr.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="fr"
    )
    da.workflow()

    print("End of Game")
