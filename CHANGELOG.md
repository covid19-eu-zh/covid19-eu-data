# Changelog

## 2020-05-22

1. Removed `documents/be` and `documents/dk` because they are bloating a lot and reached the GitHub storage hard limit (2G). The files have been moved to [covid19-eu-zh/covid19-eu-data-20200522](https://github.com/covid19-eu-zh/covid19-eu-data-20200522).
2. BE: Overwrite old files if they have the same name. Previously, we have been attaching a prefix to make copies for each day.
3. DK: Overwrite old files if they have the same name. Previously, we have been attaching a prefix to make copies for each day.

## 2020-05-12

1. NO: NO removed the updated time of the map. We have to use the the article update time in the title.

## 2020-05-09

1. NO: NO updated datetime is inconsistent between the tables and the map. We are now using map updated datetime since we switched to map values instead of table values. We also noticed some days missing. The reason is unidentified.

## 2020-04-23

1. DE: DE removed the data table from the RKI webpage and focusing on the dashboard. We switched to the dashboard API for the daily data.

## 2020-04-08

1. NL: NL started to report cases again. We have included this.
2. Scotland: Scotland moved the report to another link and also added hospitalized and intensive_care.
3. Wales: Wales stopped reporting numbers on the website. Instead, they are publishing a Tableau dashboard: https://public.tableau.com/profile/public.health.wales.health.protection#!/vizhome/RapidCOVID-19virology-Public/Headlinesummary We do have the band width to get data from Tableau. Thus Wales data collections has been stopped.
4. IE: New data source from dashboard.

## 2020-03-28

1. SI: SI Stopped updating the cumulative numbers. We will only update the cache folder for SI now.

## 2020-03-27

1. Wales: Fixed bugs related to total cases and clean up data. #38
2. AT: AT stopped reporting cases on the webpage and switched to a dashboard. We are tracking the dashboard data now. We are also caching the webpage for additional info such as deaths. #39

## 2020-03-26

1. NL: started tracking total cases from the same page. Since the sum of the cases doesn't match the report on the country level. #36