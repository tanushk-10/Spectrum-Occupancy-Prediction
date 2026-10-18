"""
Screen NIST COVID-19 spectrum dataset (mds2-2553) channels for predictability / periodicity.

Input : the per-site 'histograms/<site>.csv.gz' files from the dataset.
        Each row = one channel x one block of 60 sweeps (~10 min), with counts of
        0.5 ms band-power samples per 0.25 dB bin.  All 21 channels are present,
        including the always-busy LTE downlinks that never appear in the
        'occupancy durations' files.
Output: one CSV row per (site, channel) with data coverage, occupancy stats,
        state-persistence stats and periodicity scores, ranked.

Usage:  python screen_channels.py --hist-dir <dir with NN.csv.gz> --out results/
"""
import argparse, glob, os, sys
import numpy as np
import pandas as pd

THRESHOLDS = [-70, -65, -60, -55]      # dBm, same family as NIST's duration files
MAIN_THR = -60                          # NIST TN 2240 uses -60 dBm in its figures
BLOCK_MIN = 10.0                        # one histogram row ~= 60 sweeps ~= 10 min


def load_hist(path):
    df = pd.read_csv(path)
    df["Time"] = pd.to_datetime(df["Time"])
    cols = [c for c in df.columns if c not in ("Frequency", "Time")]
    levels = np.array([float(c) for c in cols])
    counts = df[cols].to_numpy(dtype=np.int64)
    n = counts.sum(1)
    out = df[["Frequency", "Time"]].copy()
    out["Frequency"] = out["Frequency"].round(1)
    out["N"] = n
    for t in THRESHOLDS:
        out[f"occ{t}"] = counts[:, levels >= t].sum(1) / np.maximum(n, 1)
    # mean power in dBm of the block (log-mean over bins, weighted by counts)
    mw = 10 ** (levels / 10)
    out["mean_dBm"] = 10 * np.log10(np.maximum((counts * mw).sum(1) / np.maximum(n, 1), 1e-20))
    return out


def runs(binary):
    """Lengths of consecutive runs of True / False in a boolean array."""
    if len(binary) == 0:
        return np.array([]), np.array([])
    change = np.flatnonzero(np.diff(binary.astype(np.int8))) + 1
    edges = np.r_[0, change, len(binary)]
    lengths = np.diff(edges)
    states = binary[edges[:-1]]
    return lengths[states], lengths[~states]


def acf_at(series_hourly, lag_h):
    """Autocorrelation at a given lag (hours) on an hourly grid with NaN gaps."""
    x = series_hourly.to_numpy()
    if len(x) <= lag_h + 24:
        return np.nan
    a, b = x[:-lag_h], x[lag_h:]
    m = ~np.isnan(a) & ~np.isnan(b)
    if m.sum() < 48:
        return np.nan
    a, b = a[m], b[m]
    if a.std() == 0 or b.std() == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def lomb_scargle_daily(t_hours, y):
    """Normalized Lomb-Scargle power at the 24 h period vs. the noise floor."""
    from scipy.signal import lombscargle
    m = ~np.isnan(y)
    t, y = t_hours[m], y[m]
    if len(y) < 100 or y.std() == 0:
        return np.nan, np.nan
    y = (y - y.mean()) / y.std()
    periods = np.r_[np.linspace(3, 60, 400), 24.0, 12.0, 168.0]
    w = 2 * np.pi / periods
    p = lombscargle(t, y, w, normalize=True)
    p24 = p[periods == 24.0][0]
    p12 = p[periods == 12.0][0]
    base = np.median(p[(periods > 3) & (periods < 60) & (np.abs(periods - 24) > 3) & (np.abs(periods - 12) > 2)])
    return float(p24 / max(base, 1e-9)), float(p12 / max(base, 1e-9))


def screen_site(site, df):
    rows = []
    for f, g in df.groupby("Frequency"):
        g = g.sort_values("Time")
        occ = g[f"occ{MAIN_THR}"].to_numpy()
        hours = len(g) * BLOCK_MIN / 60
        span_d = (g.Time.max() - g.Time.min()).total_seconds() / 86400

        # "state" of a block: busy if occupancy above 5 % of samples
        busy = occ > 0.05
        p_busy = busy.mean()
        # block-level entropy of state (0 = always same state, 1 = 50/50)
        ent = 0.0 if p_busy in (0, 1) else -(p_busy * np.log2(p_busy) + (1 - p_busy) * np.log2(1 - p_busy))
        rb, ri = runs(busy)

        # hourly grid for periodicity (gaps -> NaN)
        s = pd.Series(occ, index=g.Time).resample("1h").mean()
        hod = s.groupby(s.index.hour).mean()
        valid = s.dropna()
        if len(valid) > 48 and valid.std() > 0:
            # fraction of variance explained by hour-of-day mean profile
            pred = valid.index.hour.map(hod)
            r2_hod = 1 - ((valid.to_numpy() - pred.to_numpy()) ** 2).sum() / ((valid - valid.mean()) ** 2).sum()
        else:
            r2_hod = np.nan
        t_h = (s.index - s.index[0]).total_seconds().to_numpy() / 3600
        ls24, ls12 = lomb_scargle_daily(t_h, s.to_numpy())

        # same periodicity tests on the block mean power level (dBm): captures the
        # night-time power drop in always-busy LTE downlinks, which binary occupancy misses
        pw = pd.Series(g["mean_dBm"].to_numpy(), index=g.Time).resample("1h").mean()
        pw_hod = pw.groupby(pw.index.hour).mean()
        pv = pw.dropna()
        if len(pv) > 48 and pv.std() > 0:
            pp = pv.index.hour.map(pw_hod)
            r2_pw = 1 - ((pv.to_numpy() - pp.to_numpy()) ** 2).sum() / ((pv - pv.mean()) ** 2).sum()
        else:
            r2_pw = np.nan
        acf_pw = acf_at(pw, 24)
        ls24_pw, _ = lomb_scargle_daily(t_h, pw.to_numpy())

        rows.append(dict(
            site=site, freq_MHz=f, hours_data=round(hours, 1), span_days=round(span_d, 1),
            n_blocks=len(g),
            occ70=round(g["occ-70"].mean(), 4), occ60=round(occ.mean(), 4), occ55=round(g["occ-55"].mean(), 4),
            occ60_std=round(occ.std(), 4),
            p_busy=round(p_busy, 3), state_entropy=round(ent, 3),
            mean_busy_run_min=round(rb.mean() * BLOCK_MIN, 1) if len(rb) else np.nan,
            mean_idle_run_min=round(ri.mean() * BLOCK_MIN, 1) if len(ri) else np.nan,
            n_transitions=int(len(rb) + len(ri) - 1) if len(rb) + len(ri) else 0,
            acf_24h=round(acf_at(s, 24), 3) if not np.isnan(acf_at(s, 24)) else np.nan,
            acf_1h=round(acf_at(s, 1), 3) if not np.isnan(acf_at(s, 1)) else np.nan,
            r2_hour_of_day=round(r2_hod, 3) if not np.isnan(r2_hod) else np.nan,
            ls_24h=round(ls24, 1) if not np.isnan(ls24) else np.nan,
            ls_12h=round(ls12, 1) if not np.isnan(ls12) else np.nan,
            hod_peak=int(hod.idxmax()) if hod.notna().any() else np.nan,
            hod_trough=int(hod.idxmin()) if hod.notna().any() else np.nan,
            hod_range=round(float(hod.max() - hod.min()), 4) if hod.notna().any() else np.nan,
            mean_dBm=round(float(g["mean_dBm"].mean()), 1), dBm_std=round(float(g["mean_dBm"].std()), 2),
            pw_acf_24h=round(acf_pw, 3) if not np.isnan(acf_pw) else np.nan,
            pw_r2_hour_of_day=round(r2_pw, 3) if not np.isnan(r2_pw) else np.nan,
            pw_ls_24h=round(ls24_pw, 1) if not np.isnan(ls24_pw) else np.nan,
            pw_hod_range_dB=round(float(pw_hod.max() - pw_hod.min()), 2) if pw_hod.notna().any() else np.nan,
        ))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hist-dir", required=True)
    ap.add_argument("--out", default="results")
    ap.add_argument("--sites", nargs="*", default=None)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(args.hist_dir, "*.csv.gz")))
    allrows = []
    for p in files:
        site = os.path.basename(p).split(".")[0]
        if args.sites and site not in args.sites:
            continue
        print(f"[{site}] loading {p}", file=sys.stderr)
        df = load_hist(p)
        df.to_parquet(os.path.join(args.out, f"blocks_{site}.parquet"))
        res = screen_site(site, df)
        res.to_csv(os.path.join(args.out, f"screen_{site}.csv"), index=False)
        allrows.append(res)
    if allrows:
        full = pd.concat(allrows, ignore_index=True)
        # candidate score: must be intermittent (entropy) and show structure (acf_24h or r2_hod)
        full["score"] = (full.state_entropy.fillna(0)
                         * (0.5 + full.acf_24h.clip(lower=0).fillna(0) + full.r2_hour_of_day.clip(lower=0).fillna(0))
                         * np.log1p(full.hours_data) / np.log1p(24 * 14))
        full = full.sort_values("score", ascending=False)
        full.to_csv(os.path.join(args.out, "screen_all.csv"), index=False)
        pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
        print(full.to_string(index=False))


if __name__ == "__main__":
    main()
