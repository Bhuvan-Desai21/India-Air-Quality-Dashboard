# Data-quality report — city

## Volume & coverage
- rows: 17,954 -> 17,954
- date range: 2015-01-01 .. 2020-07-01
- groups (City): 11

## AQI change
- rows with old & new AQI: 15,617
- changed: 15,312 (98.0% of comparable rows)
- |delta| mean=31.2 median=16.0 p90=65.0 p99=298.0 max=430.0
- null->value: 295 | value->null: 32
- recomputed AQI max <= 500 OK

## Bucket migration

| old -> new | count |
| --- | --- |
| Good -> Moderate | 10 |
| Good -> Satisfactory | 98 |
| Good -> Unknown | 5 |
| Good -> Very Poor | 1 |
| Moderate -> Good | 59 |
| Moderate -> Poor | 213 |
| Moderate -> Satisfactory | 1502 |
| Moderate -> Severe | 4 |
| Moderate -> Unknown | 12 |
| Moderate -> Very Poor | 31 |
| Poor -> Good | 13 |
| Poor -> Moderate | 649 |
| Poor -> Satisfactory | 78 |
| Poor -> Severe | 3 |
| Poor -> Unknown | 2 |
| Poor -> Very Poor | 350 |
| Satisfactory -> Good | 825 |
| Satisfactory -> Moderate | 450 |
| Satisfactory -> Poor | 13 |
| Satisfactory -> Unknown | 12 |
| Satisfactory -> Very Poor | 7 |
| Severe -> Good | 1 |
| Severe -> Moderate | 135 |
| Severe -> Poor | 26 |
| Severe -> Satisfactory | 61 |
| Severe -> Very Poor | 151 |
| Unknown -> Good | 24 |
| Unknown -> Moderate | 115 |
| Unknown -> Poor | 21 |
| Unknown -> Satisfactory | 102 |
| Unknown -> Severe | 7 |
| Unknown -> Very Poor | 26 |
| Very Poor -> Good | 8 |
| Very Poor -> Moderate | 136 |
| Very Poor -> Poor | 156 |
| Very Poor -> Satisfactory | 44 |
| Very Poor -> Severe | 79 |
| Very Poor -> Unknown | 1 |

## Cleaning actions
- PM2.5 nulled by physical bounds: 0
- PM10 nulled by physical bounds: 0
- NO2 nulled by physical bounds: 0
- SO2 nulled by physical bounds: 0
- O3 nulled by physical bounds: 0
- CO nulled by physical bounds: 723
- NH3 nulled by physical bounds: 0
- rows flagged imputed_bound: 723
- rows flagged flagged_spike: 274

## Largest-change analysis (top 20 by |delta AQI|)

| group | date | old AQI | new AQI | delta | dominant | PM2.5 | PM10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ahmedabad | 2018-08-10 | 489.0 | 59.0 | 430 | NO2 | 34.05 | nan |
| Ahmedabad | 2018-06-23 | 495.0 | 66.0 | 429 | PM2.5 | 39.42 | nan |
| Ahmedabad | 2016-07-19 | 499.0 | 70.0 | 429 | PM2.5 | 41.39 | nan |
| Ahmedabad | 2018-07-23 | 488.0 | 72.0 | 416 | PM2.5 | 42.89 | nan |
| Ahmedabad | 2018-06-20 | 484.0 | 70.0 | 414 | PM2.5 | 41.59 | nan |
| Ahmedabad | 2018-06-16 | 492.0 | 81.0 | 411 | PM2.5 | 48.27 | nan |
| Ahmedabad | 2018-09-15 | 500.0 | 89.0 | 411 | SO2 | 18.18 | nan |
| Ahmedabad | 2016-08-04 | 494.0 | 85.0 | 409 | PM2.5 | 50.65 | nan |
| Ahmedabad | 2018-07-13 | 472.0 | 63.0 | 409 | NO2 | 36.42 | nan |
| Ahmedabad | 2018-06-24 | 486.0 | 79.0 | 407 | PM2.5 | 46.84 | nan |
| Ahmedabad | 2018-08-13 | 469.0 | 62.0 | 407 | NO2 | 32.05 | nan |
| Ahmedabad | 2016-07-28 | 468.0 | 62.0 | 406 | PM2.5 | 36.87 | nan |
| Ahmedabad | 2018-06-18 | 497.0 | 92.0 | 405 | PM2.5 | 55.21 | nan |
| Ahmedabad | 2018-06-21 | 471.0 | 66.0 | 405 | PM2.5 | 39.02 | nan |
| Ahmedabad | 2018-09-14 | 481.0 | 77.0 | 404 | SO2 | 20.82 | nan |
| Ahmedabad | 2018-07-22 | 485.0 | 82.0 | 403 | PM2.5 | 48.95 | nan |
| Ahmedabad | 2018-08-14 | 476.0 | 74.0 | 402 | PM2.5 | 44.02 | nan |
| Ahmedabad | 2018-07-26 | 474.0 | 73.0 | 401 | PM2.5 | 43.18 | nan |
| Ahmedabad | 2018-07-19 | 486.0 | 86.0 | 400 | NO2 | 44.87 | nan |
| Ahmedabad | 2018-08-26 | 482.0 | 83.0 | 399 | SO2 | 34.52 | nan |
