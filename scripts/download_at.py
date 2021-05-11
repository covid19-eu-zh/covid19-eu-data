# Beware that SSL is strict here
import logging
import os
import re

import dateutil
import pandas as pd

from utils import (_COLUMNS_ORDER, COVIDScrapper, DailyAggregator,
                   get_response)

logging.basicConfig()
logger = logging.getLogger("covid-eu-data.download.at")

AT_BUNDESLAND_URL = "https://info.gesundheitsministerium.at/data/Bundesland.js"
AT_TOTAL_URL = "https://info.gesundheitsministerium.at/data/SimpleData.js"
# AT_REPORT_URL = "https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html"
# AT_REPORT_URL = "https://info.gesundheitsministerium.gv.at/data/timeline-eimpfpass.csv"
AT_REPORT_URL = "https://info.gesundheitsministerium.gv.at/data/timeline-faelle-bundeslaender.csv"
AT_REPORT_FULL_DATA = "https://info.gesundheitsministerium.at/data/data.zip"

HOSPITALIZED = "https://www.sozialministerium.at/Informationen-zum-Coronavirus/Dashboard/Zahlen-zur-Hospitalisierung"
DAILY_FOLDER = os.path.join("dataset", "daily", "at")
CACHE_FOLDER = os.path.join("cache", "daily", "at")
AT_STATES = {
    "Bgld": "Burgenland",
    "Ktn": "Kärnten",
    "Kt": "Kärnten",
    "NÖ": "Niederösterreich",
    "OÖ": "Oberösterreich",
    "Sbg": "Salzburg",
    "Stmk": "Steiermark",
    "T": "Tirol",
    "Vbg": "Vorarlberg",
    "W": "Wien",
    "V": "Vorarlberg",
    "W+": "Wien"
}

class SARSCOV2AT(COVIDScrapper):
    def __init__(self, url=None, daily_folder=None):
        if url is None:
            url = AT_REPORT_URL

        if daily_folder is None:
            daily_folder = DAILY_FOLDER

        COVIDScrapper.__init__(self, url, country="AT", daily_folder=daily_folder)

    def extract_table(self):
        """Load data table from web page
        """

        geo_loc_key = 'nuts_2'

        # hos_df = pd.read_html(HOSPITALIZED)
        # if not hos_df:
        #     raise Exception("Could not find hospitalized table")
        # hos_df = hos_df[0]
        # hos_df.rename(
        #     columns = {
        #         "Bundesland": geo_loc_key,
        #         "Hospitalisierung": "hospitalized",
        #         "Intensivstation": "intensive_care"
        #     },
        #     inplace=True
        # )
        # hos_df.replace("Österreich gesamt", "", inplace=True)
        # # hos_df["hospitalized"] = hos_df.hospitalized.astype(int)
        # # hos_df["intensive_care"] = hos_df.intensive_care.astype(int)

        # cases_req = get_response(AT_BUNDESLAND_URL)
        # re_cases = re.compile(r'var dpBundesland = (\[.*\]);')
        # cases = re_cases.findall(cases_req.text)[0]
        # cases = json.loads(cases)
        # cases = [
        #     {geo_loc_key: AT_STATES[i["label"]], "cases": int(i["y"])}
        #     for i in cases
        # ]
        # cases_total_req = get_response(AT_TOTAL_URL)
        # re_cases_total = re.compile(r'var Erkrankungen = ["|](\d+)["|];')
        # cases_total = re_cases_total.findall(cases_total_req.text)[0]
        # cases_total = {geo_loc_key: "", "cases": cases_total}
        # cases.append(cases_total)
        # df_cases = pd.DataFrame(cases)

        # self.df = pd.merge(
        #     df_cases, hos_df, how="outer",
        #     on=geo_loc_key
        # )

        self.df  = pd.read_csv(AT_REPORT_URL, thousands='.', sep=";")
        self.df["Datum"] = self.df.Datum.apply(
            lambda x: dateutil.parser.parse(x, dayfirst=False)
        )
        # if not df:
        #     raise Exception(f'Could not find table in url: {AT_REPORT_URL}')
        self.dt = max(self.df.Datum)
        self.df = self.df.loc[self.df.Datum == self.dt]

        # rename columns
        columns = [i.replace("*", " ").replace("°", " ").split("(")[0].strip() for i in self.df.columns]
        self.df.columns = columns
        self.df.rename(
            columns={
                "Name": geo_loc_key,
                "Bevölkerung": "population",
                "BestaetigteFaelleBundeslaender": "cases",
                "Todesfaelle": "deaths",
                "Genesen": "recovered",
                "Hospitalisierung": "hospitalized",
                "Intensivstation": "intensive_care",
                "Testungen": "tests",
                "Datum": "datetime"
            }, inplace=True
        )
        self.df = self.df[[
            geo_loc_key, "cases", "deaths", "recovered", "hospitalized",
            "intensive_care", "tests", "datetime"
        ]]
        SUM_KEY = {
            "Österreich  gesamt": "",
            "Österreich gesamt": ""
        }

        self.df[geo_loc_key] = self.df[geo_loc_key].apply(lambda x: x.strip().replace(".",""))
        self.df[geo_loc_key] = self.df[geo_loc_key].str.replace('*', '')
        self.df = self.df.dropna(how="all", subset=[i for i in self.df.columns if i != geo_loc_key])
        # self.df[geo_loc_key] = self.df[geo_loc_key].apply(
        #     lambda x: AT_STATES[x] if x in AT_STATES else SUM_KEY[x]
        # )
        for col in self.df.columns:
            self.df[col] = self.df[col].apply(
                lambda x: x.replace("*", "").replace("+","").replace(".","").replace(",","").replace("^","")
                if isinstance(x, str) else x
            )

        for col in ["tests"]:
            self.df[col] = self.df[col].apply(
                lambda x: int(''.join(filter(str.isdigit, x))) if isinstance(x, str) else x
            )

        self.df.fillna("", inplace=True)
        self.df["cases"] = self.df.cases.astype(int)
        # self.df["hospitalized"] = self.df.hospitalized.astype(int)
        # self.df["intensive_case"] = self.df.intensive_case.astype(int)
        self.df["deaths"] = self.df.deaths.apply(lambda x: re.sub('[^0-9]','', x) if isinstance(x, str) else x)

        logger.info("cases:\n", self.df)

    def extract_datetime(self):
        """Get datetime of dataset
        Aktuelle Situation Österreich 04.03.2020 / 17:45 Uhr
        Stand, 10.03.2020, 08:00 Uhr
        Stand 27.03.2020, 08:00 Uhr
        Bestätigte Fälle (Stand 15.04.2020, 08:00 Uhr)
        """

        pass

    def post_processing(self):

        self.df.sort_values(by="cases", inplace=True)


def cache_content(url, dt, name):
    req = get_response(url)
    with open(
            os.path.join(CACHE_FOLDER, f"{dt}__{name}"),
            'wb'
        ) as f:
            f.write(req.content)

if __name__ == "__main__":

    # column_converter = {
    #     "state": "nuts_2"
    # }
    # drop_rows = {
    #     "state": "sum"
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

    cov_at = SARSCOV2AT()
    cov_at.workflow()

    print(cov_at.df)

    da = DailyAggregator(
        base_folder="dataset",
        daily_folder=DAILY_FOLDER,
        country="AT",
        fill=False
    )
    da.workflow()

    to_be_cached ={
        "Bezirke.js": "https://info.gesundheitsministerium.at/data/Bezirke.js",
        "Geschlechtsverteilung.js": "https://info.gesundheitsministerium.at/data/Geschlechtsverteilung.js",
        "Altersverteilung.js": "https://info.gesundheitsministerium.at/data/Altersverteilung.js",
        "SimpleData.js": "https://info.gesundheitsministerium.at/data/SimpleData.js",
        "Coronavirus.html": "https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html",
        "full_data.zip": AT_REPORT_FULL_DATA
    }
    for key,val in to_be_cached.items():
        cache_content(val, cov_at.dt.strftime("%Y%m%d%H%M"), key)

    print("End of Game")
