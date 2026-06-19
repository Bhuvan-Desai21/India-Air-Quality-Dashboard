# Data-quality report — station

## Volume & coverage
- rows: 11,208 -> 11,208
- date range: 2015-01-01 .. 2020-07-01
- groups (StationShort): 10

## AQI change
- rows with old & new AQI: 9,509
- changed: 9,252 (97.3% of comparable rows)
- |delta| mean=20.8 median=11.0 p90=42.0 p99=190.9 max=434.0
- null->value: 580 | value->null: 75
- recomputed AQI max <= 500 OK

## Bucket migration

| old -> new | count |
| --- | --- |
| Good -> Moderate | 7 |
| Good -> Satisfactory | 179 |
| Good -> Unknown | 10 |
| Good -> Very Poor | 1 |
| Moderate -> Good | 73 |
| Moderate -> Poor | 53 |
| Moderate -> Satisfactory | 1074 |
| Moderate -> Severe | 1 |
| Moderate -> Unknown | 6 |
| Moderate -> Very Poor | 17 |
| Poor -> Good | 34 |
| Poor -> Moderate | 61 |
| Poor -> Satisfactory | 32 |
| Poor -> Severe | 6 |
| Poor -> Unknown | 1 |
| Poor -> Very Poor | 16 |
| Satisfactory -> Good | 1135 |
| Satisfactory -> Moderate | 241 |
| Satisfactory -> Poor | 5 |
| Satisfactory -> Severe | 2 |
| Satisfactory -> Unknown | 57 |
| Satisfactory -> Very Poor | 3 |
| Severe -> Good | 8 |
| Severe -> Moderate | 4 |
| Severe -> Satisfactory | 11 |
| Severe -> Very Poor | 2 |
| Unknown -> Good | 115 |
| Unknown -> Moderate | 211 |
| Unknown -> Poor | 13 |
| Unknown -> Satisfactory | 220 |
| Unknown -> Severe | 5 |
| Unknown -> Very Poor | 16 |
| Very Poor -> Good | 15 |
| Very Poor -> Moderate | 10 |
| Very Poor -> Poor | 6 |
| Very Poor -> Satisfactory | 11 |
| Very Poor -> Severe | 3 |
| Very Poor -> Unknown | 1 |

## Cleaning actions
- PM2.5 nulled by physical bounds: 0
- PM10 nulled by physical bounds: 0
- NO2 nulled by physical bounds: 0
- SO2 nulled by physical bounds: 0
- O3 nulled by physical bounds: 0
- CO nulled by physical bounds: 215
- NH3 nulled by physical bounds: 0
- rows flagged imputed_bound: 215
- rows flagged flagged_spike: 271

## Largest-change analysis (top 20 by |delta AQI|)

| group | date | old AQI | new AQI | delta | dominant | PM2.5 | PM10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Peenya | 2018-07-10 | 51.0 | 485.0 | 434 | PM2.5 | 461.38 | nan |
| BWSSB Kadabesanahalli | 2017-02-03 | 477.0 | 51.0 | 426 | O3 | 21.21 | nan |
| BWSSB Kadabesanahalli | 2016-07-01 | 464.0 | 45.0 | 419 | O3 | 17.6 | nan |
| BWSSB Kadabesanahalli | 2017-02-06 | 480.0 | 61.0 | 419 | O3 | 22.66 | nan |
| BWSSB Kadabesanahalli | 2016-07-03 | 458.0 | 42.0 | 416 | O3 | 17.41 | nan |
| Peenya | 2015-07-06 | 452.0 | 38.0 | 414 | PM2.5 | 22.7 | nan |
| BWSSB Kadabesanahalli | 2017-02-04 | 476.0 | 62.0 | 414 | O3 | 20.93 | nan |
| BWSSB Kadabesanahalli | 2017-02-05 | 468.0 | 59.0 | 409 | O3 | 22.47 | nan |
| BWSSB Kadabesanahalli | 2016-06-28 | 444.0 | 38.0 | 406 | O3 | 13.83 | nan |
| BWSSB Kadabesanahalli | 2017-02-07 | 471.0 | 66.0 | 405 | O3 | 25.04 | nan |
| BWSSB Kadabesanahalli | 2016-07-04 | 433.0 | 33.0 | 400 | O3 | 18.91 | nan |
| BWSSB Kadabesanahalli | 2016-06-19 | 442.0 | 43.0 | 399 | PM2.5 | 25.97 | nan |
| BWSSB Kadabesanahalli | 2016-06-18 | 453.0 | 54.0 | 399 | PM2.5 | 31.58 | nan |
| BWSSB Kadabesanahalli | 2016-06-24 | 461.0 | 66.0 | 395 | O3 | 10.32 | nan |
| BWSSB Kadabesanahalli | 2016-07-02 | 441.0 | 54.0 | 387 | PM2.5 | 31.81 | nan |
| BWSSB Kadabesanahalli | 2015-08-13 | 402.0 | 19.0 | 383 | PM2.5 | 11.49 | nan |
| BWSSB Kadabesanahalli | 2015-07-24 | 398.0 | 23.0 | 375 | PM2.5 | 13.64 | nan |
| BWSSB Kadabesanahalli | 2016-06-30 | 412.0 | 40.0 | 372 | O3 | 12.52 | nan |
| BWSSB Kadabesanahalli | 2019-09-16 | 98.0 | 463.0 | 365 | PM2.5 | 405.36 | nan |
| BWSSB Kadabesanahalli | 2015-07-21 | 384.0 | 25.0 | 359 | PM2.5 | 15.11 | nan |
