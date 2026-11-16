# Channel screening: sites 02 and 12

This is a first-pass shortlist from the existing 10-minute NIST histogram data. The CSV files contain all channel-level results; the examples below are the highest-ranked channels at each site.

| Site | Channel (MHz) | Screening score | Blocks often busy | 24-hour similarity |
|---:|---:|---:|---:|---:|
| 02 | 2462 | 1.275 | 34.5% | 0.734 |
| 02 | 2437 | 1.251 | 61.2% | 0.623 |
| 12 | 751 | 1.183 | 20.3% | 0.748 |
| 12 | 866.3 | 1.063 | 81.1% | 0.518 |
| 12 | 2462 | 0.997 | 68.5% | 0.451 |

`Blocks often busy` is the share of 10-minute blocks whose -60 dBm occupancy exceeded 5%. `24-hour similarity` compares occupancy on an hourly grid with occupancy one day later; values closer to 1 indicate a stronger relationship.

The screening score combines how often a channel changes between busy and quiet, its daily structure, and the amount of data available. It is a way to prioritize channels for follow-up, not a prediction-accuracy measure. The shortlist should be checked against the per-look results and validated on held-out data before drawing modeling conclusions.