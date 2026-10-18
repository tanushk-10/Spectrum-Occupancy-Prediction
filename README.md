# Spectrum-Occupancy-Prediction
By: Tanush Kandpal, Kate Sarycheva, Lakshmi Koganti

Predicting channel occupancy on the NIST "Distributed Sensing of Radio Spectrum Occupancy Amid COVID-19" dataset
(https://data.nist.gov/od/id/mds2-2553, NIST TN 2240).

- `results/candidates.md` – which channels/sites look worth modelling and why
- `scripts/` – screening scripts and the downloader
- `data/` – NIST files go here (gitignored, see `scripts/fetch_nist.sh`)

Needs Python 3 with pandas, numpy, scipy, pyarrow.
