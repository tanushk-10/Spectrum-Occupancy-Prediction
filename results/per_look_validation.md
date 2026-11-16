# My per-look data summary

A look is one brief measurement on one channel. I processed the NIST readings for sites 02 and 12 and summarized channel coverage, how often the sensor returned to each channel, long gaps, and readings above -70 dBm.

Each look normally contains 210 power readings -- Zero and negative readings as below the threshold and leave missing readings out. For mean and maximum signal strength in dBm, we will only use positive readings only and we have to make sure that we average the power in mW before converting the mean to dBm.

I also checked the channel order in the first 20,000 looks. For comparison, I added up the -70 dBm burst durations in NIST's event file and divided by sampled time and then matched the channel labels to the nearest event-file frequency within 5.1 MHz. `not listed` just means NIST's event file has no burst rows for that channel; it does not mean measured occupancy was zero. The two percentages can be difference since they are measureing activity in different ways.

## Site 02

- Sensor looks: 4,760,511
- Dates covered: 2020-06-15 to 2020-08-11
- Channels: 21
- Samples per look: 210 in every look (4,760,511 looks)
- Typical time between looks on a channel: 10.2 seconds
- I found a different channel order in each of 952 complete sweeps I checked.

| Channel (MHz) | Looks | Readings above -70 dBm | Typical revisit | Gaps over 1 min | Duration-based -70 dBm estimate |
|---:|---:|---:|---:|---:|---:|
| 702 | 226,691 | 0.01% | 10.2 s | 19 | 0.01% |
| 709 | 226,691 | 0.00% | 10.2 s | 19 | 0.00% |
| 734 | 226,691 | 24.54% | 10.2 s | 19 | not listed |
| 739 | 226,691 | 22.08% | 10.2 s | 19 | not listed |
| 751 | 226,691 | 2.68% | 10.2 s | 19 | not listed |
| 782 | 226,691 | 0.00% | 10.2 s | 19 | 0.00% |
| 821 | 226,691 | 0.00% | 10.2 s | 19 | 0.00% |
| 842 | 226,691 | 0.00% | 10.2 s | 19 | 0.00% |
| 866 | 226,691 | 14.80% | 10.2 s | 19 | not listed |
| 888 | 226,691 | 0.00% | 10.2 s | 19 | not listed |
| 2410 | 226,691 | 0.17% | 10.2 s | 19 | 0.16% |
| 2440 | 226,691 | 4.84% | 10.2 s | 19 | 4.48% |
| 2460 | 226,691 | 3.12% | 10.2 s | 19 | 2.92% |
| 2700 | 226,691 | 0.00% | 10.2 s | 19 | 0.00% |
| 5170 | 226,691 | 0.00% | 10.2 s | 19 | 0.00% |
| 5190 | 226,691 | 0.01% | 10.2 s | 19 | 0.01% |
| 5210 | 226,691 | 0.01% | 10.2 s | 19 | 0.01% |
| 5230 | 226,691 | 0.01% | 10.2 s | 19 | 0.01% |
| 5240 | 226,691 | 0.02% | 10.2 s | 19 | 0.02% |
| 5780 | 226,691 | 0.01% | 10.2 s | 19 | 0.01% |
| 5800 | 226,691 | 0.00% | 10.2 s | 19 | 0.00% |

### Site-wide gaps over 2 minutes
- 2020-07-01 09:17:34 to 2020-07-06 09:09:24: 5.0 days without recorded looks
- 2020-07-23 22:15:30 to 2020-07-27 08:05:59: 3.4 days without recorded looks
- 2020-08-07 08:55:45 to 2020-08-10 16:35:08: 3.3 days without recorded looks
- 2020-07-30 17:53:31 to 2020-08-02 19:37:15: 3.1 days without recorded looks
- 2020-07-10 12:15:17 to 2020-07-13 07:20:13: 2.8 days without recorded looks
## Site 12

- Sensor looks: 4,918,557
- Dates covered: 2020-06-12 to 2020-08-01
- Channels: 21
- Samples per look: 210 in every look (4,918,557 looks)
- Typical time between looks on a channel: 10.3 seconds
- I found a different channel order in each of 952 complete sweeps I checked.

| Channel (MHz) | Looks | Readings above -70 dBm | Typical revisit | Gaps over 1 min | Duration-based -70 dBm estimate |
|---:|---:|---:|---:|---:|---:|
| 702 | 234,217 | 0.00% | 10.2 s | 13 | 0.00% |
| 709 | 234,217 | 0.97% | 10.3 s | 13 | 0.91% |
| 734 | 234,217 | 100.00% | 10.3 s | 13 | not listed |
| 739 | 234,217 | 99.46% | 10.3 s | 13 | not listed |
| 751 | 234,217 | 90.48% | 10.3 s | 13 | not listed |
| 782 | 234,217 | 0.08% | 10.3 s | 13 | 0.07% |
| 821 | 234,217 | 0.31% | 10.3 s | 13 | 0.27% |
| 842 | 234,217 | 0.13% | 10.3 s | 13 | 0.12% |
| 866 | 234,217 | 87.17% | 10.3 s | 13 | not listed |
| 888 | 234,217 | 36.34% | 10.3 s | 13 | not listed |
| 2410 | 234,217 | 5.49% | 10.3 s | 13 | 5.24% |
| 2440 | 234,217 | 5.03% | 10.3 s | 13 | 4.64% |
| 2460 | 234,217 | 10.34% | 10.2 s | 13 | 9.62% |
| 2700 | 234,217 | 0.00% | 10.3 s | 13 | 0.00% |
| 5170 | 234,217 | 0.00% | 10.3 s | 13 | 0.00% |
| 5190 | 234,217 | 0.04% | 10.3 s | 13 | 0.04% |
| 5210 | 234,217 | 0.01% | 10.3 s | 13 | 0.01% |
| 5230 | 234,217 | 0.02% | 10.3 s | 14 | 0.02% |
| 5240 | 234,217 | 0.01% | 10.3 s | 13 | 0.01% |
| 5780 | 234,217 | 0.01% | 10.3 s | 13 | 0.01% |
| 5800 | 234,217 | 0.01% | 10.3 s | 13 | 0.01% |

### Site-wide gaps over 2 minutes
- 2020-07-03 03:32:17 to 2020-07-07 13:28:28: 4.4 days without recorded looks
- 2020-06-18 23:05:37 to 2020-06-22 09:09:22: 3.4 days without recorded looks
- 2020-07-26 09:47:28 to 2020-07-29 15:48:28: 3.3 days without recorded looks
- 2020-07-17 10:57:55 to 2020-07-20 12:57:13: 3.1 days without recorded looks
- 2020-06-12 13:56:47 to 2020-06-15 15:45:40: 3.1 days without recorded looks