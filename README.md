# covid19-eu-data

## Status

| Country | Status |
| ------------- | ------------- |
| AT | ![CI Download AT Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20AT%20Data/badge.svg) |
| BE | ![CI Download BE PDF](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20BE%20PDF/badge.svg) |
| CZ | ![CI Download CZ Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20CZ%20Data/badge.svg) |
| DE | ![CI Download DE SARS-COV-2 Cases from RKI](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20DE%20SARS-COV-2%20Cases%20from%20RKI/badge.svg) |
| ES  | ![CI Download ES PDF Files](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20ES%20PDF%20Files/badge.svg)  |
| FR  | ![CI Download FR Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20FR%20Data/badge.svg) |
| NL | ![CI Download NL SARS-COV-2 Cases from volksgezondheidenzorg](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20NL%20SARS-COV-2%20Cases%20from%20volksgezondheidenzorg/badge.svg) |
| PL | ![CI Download PL Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20PL%20Data/badge.svg) |
| SE | ![CI Download SE](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20SE/badge.svg) |
| UK | ![CI Download England Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20England%20Data/badge.svg)  ![CI Download Scotland Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20Scotland%20Data/badge.svg)  |
| EU(ECDC) | ![CI Download All EU from ECDC](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20All%20EU%20from%20ECDC/badge.svg) |
| IT | ![CI Download IT Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20IT%20Data/badge.svg) |


## Countries

### AT

Data source:https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html

Caveats:

1. We started tracking the recovered and the deaths on 2020-03-13.

### NL

Data source: https://www.volksgezondheidenzorg.info/onderwerp/infectieziekten/regionaal-internationaal/coronavirus-covid-19#node-coronavirus-covid-19-meldingen

Caveats:

1. NL doesn't publish the time of the data release. We use 00:00 of the day to denote the release time though it doesn't indicate the actual update time.


### UK

#### England


1. In the first few days of reporting, data of England is not always a number. To solve this problem, we added two columns, `cases_lower` and `cases_upper`, to reflect the range of the number of cases.
2. England switched to ArcGIS later. We are downloading the CSV file directly.

#### Scotland

[Source: Scottish Gov](https://www.gov.scot/coronavirus-covid-19/)

#### Wales

[Source: Public Health Wales](https://phw.nhs.wales/news/public-health-wales-statement-on-novel-coronavirus-outbreak/)

#### Northern Ireland

[Source: Public Health Agency - HSCNI](https://www.publichealth.hscni.net/news/covid-19-coronavirus#situation-in-northern-ireland)


### IT

[Source: PCM-DPC GitHub](https://github.com/pcm-dpc/COVID-19/blob/master/dati-json/dpc-covid19-ita-province-latest.json)

Set the `-f` flag to `true` for `scripts/download_it.py` to redownload all dates.
