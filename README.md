# covid19-eu-data

`covid19-eu-data` is a dataset repository for COVID-19/SARS-CoV-2 cases in Europe. We pull data from official government websites regularly using the open-source scripts inside the repository.

## Update Status

**Commit Status**:

![](https://img.shields.io/github/last-commit/covid19-eu-zh/covid19-eu-data/master) ![](https://img.shields.io/github/commit-activity/w/covid19-eu-zh/covid19-eu-data)

**Workflow status by countries**:

| Country | Status |
| ------------- | ------------- |
| AT | ![CI Download AT Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20AT%20Data/badge.svg) |
| BE | ![CI Download BE PDF](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20BE%20PDF/badge.svg) |
| CZ | ![CI Download CZ Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20CZ%20Data/badge.svg) |
| DE | ![CI Download DE SARS-COV-2 Cases from RKI](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20DE%20SARS-COV-2%20Cases%20from%20RKI/badge.svg) |
| ES  | ![CI Download ES PDF Files](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20ES%20PDF%20Files/badge.svg)  |
| FR  | ![CI Download FR Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20FR%20Data/badge.svg) |
| IT | ![CI Download IT Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20IT%20Data/badge.svg) |
| NL | ![CI Download NL SARS-COV-2 Cases from volksgezondheidenzorg](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20NL%20SARS-COV-2%20Cases%20from%20volksgezondheidenzorg/badge.svg) |
| PL | ![CI Download PL Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20PL%20Data/badge.svg) |
| SE | ![CI Download SE](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20SE/badge.svg) |
| UK | ![CI Download England Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20England%20Data/badge.svg)  ![CI Download Scotland Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20Scotland%20Data/badge.svg)  |
| EU(ECDC) | ![CI Download All EU from ECDC](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20All%20EU%20from%20ECDC/badge.svg) |


## Dataset

### Tabular Data

The **tabular data** files are located in `dataset` folder:

```
dataset
├── covid-19-at.csv              # All records of in AT
├── covid-19-cz.csv
├── covid-19-de.csv
├── covid-19-ecdc.csv
├── covid-19-england.csv
├── covid-19-fr.csv
├── covid-19-it.csv
├── covid-19-nl.csv
├── covid-19-pl.csv
├── covid-19-scotland.csv
├── covid-19-se.csv
├── covid-19-uk.csv
├── covid-19-wales.csv
└── daily                        # Daily updates of the data
    ├── at
    ├── cz
    ├── de
    ├── ecdc
    ├── england
    ├── fr
    ├── it
    ├── nl
    ├── pl
    ├── scotland
    ├── se
    ├── uk
    └── wales
```

> The metadata for the tabular data is found in `.dataherb/metadata.yml`.

### Other Data

Some of the countries publish more than simple tabular data. We cache the files in `documents` folder.

```
documents
└── daily
    ├── be
    ├── cz
    ├── es
    └── fr
```

### Scrapers

The scripts that are being used to update the data are located in `scripts` folder. Most of the scripts require the `utils.py` module to run. Create a new environment and run `pip install -r requirements.txt` to install the requirements.

### Workflows

The workflows that update the dataset are defined in `.github/workflows`.


## Data Sources and Comments

### AT

[![](https://img.shields.io/badge/Data%20Source-sozialministerium.at-informational)](https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html)


Caveats:

1. We started tracking the recovered population and the deaths on 2020-03-13.

### BE

[![](https://img.shields.io/badge/Data%20Source-epidemio.wiv--isp.be-informational)](https://epidemio.wiv-isp.be/ID/Pages/2019-nCoV_epidemiological_situation.aspx)

1. Only PDF files of the records are downloaded.

### NL

[![](https://img.shields.io/badge/Data%20Source-volksgezondheidenzorg.info-informational)](https://www.volksgezondheidenzorg.info/onderwerp/infectieziekten/regionaal-internationaal/coronavirus-covid-19#node-coronavirus-covid-19-meldingen)

Caveats:

1. NL doesn't publish the time of the data release. We use 00:00 of the day to denote the release time though it doesn't indicate the actual update time.


### UK


#### England

[![](https://img.shields.io/badge/Data%20Source-official_arcgis-informational)](https://www.arcgis.com/sharing/rest/content/items/b684319181f94875a6879bbc833ca3a6/data)

1. In the first few days of reporting (before 2020-03-11), data of England is not always a number. To solve this problem, we added two columns, `cases_lower` and `cases_upper`, to reflect the range of the number of cases.
2. England switched to ArcGIS later. We are downloading the CSV file directly.

#### Scotland

[![](https://img.shields.io/badge/Data%20Source-gov.scot-informational)](https://www.gov.scot/coronavirus-covid-19/)


#### Wales

[![](https://img.shields.io/badge/Data%20Source-phw.nhs.wales-informational)](https://phw.nhs.wales/news/public-health-wales-statement-on-novel-coronavirus-outbreak/)

1. Wales stopped publishing detailed data on 2020-03-17.


#### Northern Ireland

[![](https://img.shields.io/badge/Data%20Source-publichealth.hscni.net-informational)](https://www.publichealth.hscni.net/news/covid-19-coronavirus#situation-in-northern-ireland)

Northern Ireland does not publish detailed data.


### IT

[![](https://img.shields.io/badge/Data%20Source-pcm--dpc/COVID--19-informational)](https://github.com/pcm-dpc/COVID-19/blob/master/dati-json/dpc-covid19-ita-province-latest.json)


1. The data source also provides the whole time-series data. Set the `-f` flag to `true` for `scripts/download_it.py` to redownload all dates.


## Community

**Bugs and requests**: submit them through the project's issues tracker.
[![Issues](http://img.shields.io/github/issues/covid19-eu-zh/covid19-eu-data.svg)]( https://github.com/covid19-eu-zh/covid19-eu-data/issues )

**Telegram Channel (in Chinese)**: ask them at StackOverflow with the tag *REPO*.
[![Chat](http://img.shields.io/badge/telegram-covid19__eu__zh__c-blue.svg)](https://t.me/s/covid19_eu_zh_c)
