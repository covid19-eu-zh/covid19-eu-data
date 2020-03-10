# covid19-eu-data

## Status

| Country | Status |
| ------------- | ------------- |
| AT | ![CI Download AT Data](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20AT%20Data/badge.svg) |
| DE | ![CI Download DE SARS-COV-2 Cases from RKI](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20DE%20SARS-COV-2%20Cases%20from%20RKI/badge.svg) |
| ES  | ![CI Download ES PDF Files](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20ES%20PDF%20Files/badge.svg)  |
| FR  | ![CI Download FR PDF Files](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20FR%20PDF%20Files/badge.svg)  |
| NL | ![CI Download NL SARS-COV-2 Cases from volksgezondheidenzorg](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20NL%20SARS-COV-2%20Cases%20from%20volksgezondheidenzorg/badge.svg) |
| UK | ![CI Download England SARS-COV-2 Cases from Public Health England](https://github.com/covid19-eu-zh/covid19-eu-data/workflows/CI%20Download%20England%20SARS-COV-2%20Cases%20from%20Public%20Health%20England/badge.svg) |

## Countries

### NL

Data source: https://www.volksgezondheidenzorg.info/onderwerp/infectieziekten/regionaal-internationaal/coronavirus-covid-19#node-coronavirus-covid-19-meldingen

Caveats:

1. NL doesn't publish the time of the data release. We use 00:00 of the day to denote the release time though it doesn't indicate the actual update time.


### UK

England data is not always a number. To solve this problem, we added two columns, `cases_lower` and `cases_upper`, to reflect the range of the number of cases.
