# Which channels are worth testing for periodicity?

Quick notes from screening the NIST COVID-19 spectrum dataset (sites 02, 04, 08, 12 and the hospital so far).
The other sites are still downloading because NIST's server keeps going down.

## The short version

**Site 08 is too small.** It only has ~32 hours of actual sensing, spread over two months.
Sites 02 and 12 have ~650 hours each (most of June–August 2020, 24/7). That's where daily patterns show up.

**Good candidates:**

| Site | Channel | What it looks like |
|---|---|---|
| 02 | 2462 MHz (WiFi ch 11) | Clearest daily cycle. Peaks around 6 pm, quiet at 1 am. 24h autocorrelation 0.70 |
| 02 | 2437 MHz (WiFi ch 6) | Busy all day, drops at night. 24h autocorrelation 0.59 |
| 12 | 821 MHz (LTE uplink) | Only active during work hours (noon–7 pm). Very on/off |
| 12 | 709 MHz (LTE uplink) | Busy evenings and nights, dead 2–6 am |
| 12 | 782 MHz (LTE uplink) | Daytime only |
| 02 | 5775 MHz (5 GHz WiFi) | Very bursty, weaker daily cycle |
| 12 | 5190 MHz (5 GHz WiFi) | Only Friday/Saturday evenings. Weekly pattern, not daily |

Kate's site-08 picks (709, 782, 821 MHz) are the right *type* of channel, they just need a site with more data.

## Things to know about the dataset

- **Don't download the time-series tarballs** (10–24 GB each). The `histograms/` files (one row per channel per ~10 min)
  and `occupancy durations/` files (one row per burst) are 1–500 MB and have everything we need for screening.
- The sensor sits on each channel for 300 ms, keeps the last 105 ms (210 samples of 0.5 ms), then moves on.
  One full sweep of 21 channels takes ~10 s. Channel order is shuffled every sweep.
- **LTE downlinks (734, 739, 751, 866 MHz) are on 100% of the time.** Nothing to predict about busy/idle there,
  but their power level drops a few dB at night, so power could be the target instead.
- 2695 MHz is a passive band (always empty), 887.5 MHz is basically always empty too.
- Bursts are short: median 1 ms, 90th percentile 2–4 ms, on every channel at every site.

## How to rerun

```
python scripts/screen_channels.py --hist-dir data/hist --out results   # all 21 channels, 10-min blocks
python scripts/screen_events.py  --occ-dir  data/occ  --out results    # burst-level
bash scripts/fetch_nist.sh                                              # downloads + reruns both as sites arrive
```

Full tables: `results/screen_all.csv` and `results/events_all_-70.csv`.
Columns: `acf_24h` = how similar each hour is to the same hour yesterday, `r2_hour_of_day` = how much a fixed
time-of-day profile explains, `ls_24h` = Lomb-Scargle peak at 24 h vs noise, `state_entropy` = 1 means 50/50 busy/idle.
