# covid19-eu-data

`covid19-eu-data` is a dataset repository for COVID-19/SARS-CoV-2 cases in Europe. We pull data from official government websites regularly using the open-source scripts inside the repository.

**If you would like to help or track the progress of this project**, checkout our roadmap.

[![](https://img.shields.io/badge/roadmap-data--pipeline-blueviolet)](https://github.com/orgs/covid19-eu-zh/projects/1)

## Update Status

**Commit Status**:

![](https://img.shields.io/github/last-commit/covid19-eu-zh/covid19-eu-data/master) ![](https://img.shields.io/github/commit-activity/w/covid19-eu-zh/covid19-eu-data)

**Workflow status by countries**:

| Country | Status | Data Source |
| ------------- | ------------- | --- |
| AT | ![CI Download AT Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20AT%20Data/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-sozialministerium.at-informational)](https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html) |
| BE | ![CI Download BE PDF](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20BE%20PDF/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-epidemio.wiv--isp.be-informational)](https://epidemio.wiv-isp.be/ID/Pages/2019-nCoV_epidemiological_situation.aspx) |
| CH | ![CI Download CH Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20CH%20Data/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-epidemio.wiv--daenuprobst/covid19--cases--switzerland-informational)](https://github.com/daenuprobst/covid19-cases-switzerland) |
| CZ | ![CI Download CZ Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20CZ%20Data/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-onemocneni--aktualne.mzcr.cz-informational)](https://onemocneni-aktualne.mzcr.cz/covid-19) |
| DE | ![CI Download DE SARS-COV-2 Cases from RKI](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20DE%20SARS-COV-2%20Cases%20from%20RKI/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-rki.de-informational)](https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Fallzahlen.html) |
| DK  | ![CI Download DK PDF](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20DK%20PDF/badge.svg)  | [![](https://img.shields.io/badge/Data%20Source-ssi.dk-informational)](https://www.ssi.dk/aktuelt/sygdomsudbrud/coronavirus/covid-19-i-danmark-epidemiologisk-overvaagningsrapport) |
| ES  | ![CI Download ES PDF Files](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20ES%20PDF%20Files/badge.svg)  | [![](https://img.shields.io/badge/Data%20Source-mscbs.gob.es-informational)](http://www.mscbs.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov-China/situacionActual.htm) |
| FR  | ![CI Download FR PDF](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20FR%20PDF/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-santepubliquefrance.fr-informational)](https://www.santepubliquefrance.fr/maladies-et-traumatismes/maladies-et-infections-respiratoires/infection-a-coronavirus/articles/infection-au-nouveau-coronavirus-sars-cov-2-covid-19-france-et-monde) |
| GR | ![CI Download GR PDF](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20GR%20PDF/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-eody.gov.gr-informational)](https://eody.gov.gr/neos-koronaios-covid-19/) |
| HU  | ![CI Download HU Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20HU%20Data/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-koronavirus.gov.hu-informational)](https://koronavirus.gov.hu/) |
| IE | ![CI Download IE Data and PDF](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20IE%20Data%20and%20PDF/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-hpsc.ie-informational)](https://www.hpsc.ie/a-z/respiratory/coronavirus/novelcoronavirus/casesinireland/) |
| IT | ![CI Download IT Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20IT%20Data/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-pcm--dpc/COVID--19-informational)](https://github.com/pcm-dpc/COVID-19/blob/master/dati-json/dpc-covid19-ita-province-latest.json) |
| NL | ![CI Download NL SARS-COV-2 Cases from volksgezondheidenzorg](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20NL%20SARS-COV-2%20Cases%20from%20volksgezondheidenzorg/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-volksgezondheidenzorg.info-informational)](https://www.volksgezondheidenzorg.info/onderwerp/infectieziekten/regionaal-internationaal/coronavirus-covid-19#node-coronavirus-covid-19-meldingen) |
| NO | ![CI Download NO Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20NO%20Data/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-fhi.no-informational)](https://www.fhi.no/en/id/infectious-diseases/coronavirus/daily-reports/daily-reports-COVID19/) |
| PL | ![CI Download PL Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20PL%20Data/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-gov.pl-informational)](https://www.gov.pl/web/koronawirus/wykaz-zarazen-koronawirusem-sars-cov-2) |
| PT | ![CI Download PT PDF](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20PT%20PDF/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-covid19.min--saude.pt-informational)](https://covid19.min-saude.pt/relatorio-de-situacao/) |
| SE | ![CI Download SE](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20SE/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-folkhalsomyndigheten.se-informational)](https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/aktuellt-epidemiologiskt-lage/)  |
| SI | ![CI Download SI Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20SI%20Data/badge.svg) | [![](https://img.shields.io/badge/Data%20Source-gov.si-informational)](https://www.gov.si/en/topics/coronavirus-disease-covid-19/) |
| UK | ![CI Download Scotland Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20Scotland%20Data/badge.svg)  | [![](https://img.shields.io/badge/Data%20Source-official_arcgis-informational)](https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data) [![](https://img.shields.io/badge/Data%20Source-gov.scot-informational)](https://www.gov.scot/coronavirus-covid-19/) [![](https://img.shields.io/badge/Data%20Source-phw.nhs.wales-informational)](https://phw.nhs.wales/news/public-health-wales-statement-on-novel-coronavirus-outbreak/) [![](https://img.shields.io/badge/Data%20Source-publichealth.hscni.net-informational)](https://www.publichealth.hscni.net/news/covid-19-coronavirus#situation-in-northern-ireland) |
| EU(ECDC) | ![CI Download All EU from ECDC](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20All%20EU%20from%20ECDC/badge.svg) |  [![](https://img.shields.io/badge/Data%20Source-ecdc.europa.eu-informational)](https://www.ecdc.europa.eu/en/cases-2019-ncov-eueea) |


## Dataset

### Tabular Data

The **tabular data** files are located in `dataset` folder. The folder `dataset/daily` holds the daily updates in each country.

> The metadata for the tabular data is found in `.dataherb/metadata.yml`.

### Other Data

Some of the countries publish more than simple tabular data. We cache the files in `documents` folder.

### Scrapers

The scripts that are being used to update the data are located in `scripts` folder. Most of the scripts require the `utils.py` module to run. Create a new environment and run `pip install -r requirements.txt` to install the requirements.

### Workflows

The workflows that update the dataset are defined in `.github/workflows`. The python scripts are scheduled to run on GitHub Actions.

## Notes

### AT

Caveats:

1. We started tracking the recovered population and the deaths on 2020-03-13.

### BE

1. Only PDF files of the records are downloaded.

### DE

1. For technical reasons, no data was transmitted from Hamburg on March 25th, 2020.

There is [a repo](https://github.com/averissimo/covid19.de.data) cleaning up the raw data on ArcGis.

### FR

1. France stopped updating the case tables on the webpage on 2020-03-26. We went back to the PDF files.

### NL

Caveats:

1. NL doesn't publish the time of the data release. We use 00:00 of the day to denote the release time though it doesn't indicate the actual update time.

### UK

**We stopped tracking UK data.**

1. UK is already publishing data in an easy-to-use format. [Click here for the full data](https://coronavirus.data.gov.uk/#countries)
2. There is already a very good github repo cleaning up the data. [Click here for the repo.](https://github.com/tomwhite/covid-19-uk-data)

#### Scotland

1. Starting from 2020-04-08, Scotland doesn't report numbers less than 5. So missing value in Scotland dataset starting from 2020-04-08 indicates a number less than 5.

#### England

1. In the first few days of reporting (before 2020-03-11), data of England is not always a number. To solve this problem, we added two columns, `cases_lower` and `cases_upper`, to reflect the range of the number of cases.
2. England switched to ArcGIS later. We are downloading the CSV file directly.

#### Wales

1. Wales stopped publishing detailed data on 2020-03-17.
2. Wales switched to Tableau on 2020-04-08. https://public.tableau.com/profile/public.health.wales.health.protection#!/vizhome/RapidCOVID-19virology-Public/Headlinesummary

#### Northern Ireland

Northern Ireland does not publish detailed data.

### IT

1. The data source also provides the whole time-series data. Set the `-f` flag to `true` for `scripts/download_it.py` to redownload all dates.


## Community

**Bugs and requests**: PRs are welcome.

[![Issues](http://img.shields.io/github/issues/covid19-eu-zh/covid19-eu-data.svg)]( https://github.com/covid19-eu-zh/covid19-eu-data/issues )

**Telegram Channel (in Chinese)**: [新冠肺炎欧洲中文臺](https://t.me/s/covid19_eu_zh_c)

[![Chat](http://img.shields.io/badge/telegram-covid19__eu__zh__c-blue.svg)](https://t.me/s/covid19_eu_zh_c)
