# Spectrum-Occupancy-Prediction
By: Tanush Kandpal, Kate Sarycheva, Lakshmi Koganti

Predicting channel occupancy on the NIST "Distributed Sensing of Radio Spectrum Occupancy Amid COVID-19" dataset
(https://data.nist.gov/od/id/mds2-2553, NIST TN 2240).

- `results/candidates.md` – which channels/sites look worth modelling and why
- `results/per_look_screening/README.md` – summary and interpretation of the updated site-02/site-12 screening
- `scripts/` – screening scripts and the downloader
- `data/` – NIST files go here (gitignored, see `scripts/fetch_nist.sh`)

Needs Python 3 with pandas, numpy, scipy, pyarrow.

## Per-look time-series processing

The denoised time-series archives are large site-level tarballs; each archive contains
one or more day CSVs. The processor reads the gzip tar stream and processes CSV chunks
without extracting the archive:

```
python scripts/process_timeseries.py --archive data/02.tar.gz --site 02 --output results/looks_02.parquet
python scripts/process_timeseries.py --archive data/12.tar.gz --site 12 --output results/looks_12.parquet
python scripts/validate_timeseries.py
python scripts/screen_channels.py --hist-dir data/hist --out results/per_look_screening --sites 02 12
```

Each source row contains `Time`, `Frequency`, `Sweep`, and 210 nominal 0.5 ms power
samples in mW. `n_samples` counts finite readings; zero and negative denoised values
are retained in threshold denominators as below-threshold measurements, while missing
or non-finite readings are excluded. dBm summaries use positive mW readings only, and
the mean is computed in linear mW before conversion. Looks with no positive readings
have missing dBm summaries. The generated validation report compares sampled occupancy
to the summed durations in NIST's occupancy-duration files; the aggregation definitions
can differ. Raw archives, downloaded inputs, and Parquet outputs are not committed.
