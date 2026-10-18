"""
Event-based channel screen using the NIST 'occupancy durations/<site>.csv.gz' files.

Each row of those files is one transmission burst: (Frequency, Time, duration in
seconds above each threshold -75..-50 dBm).  Bursts are binned to BIN minutes,
giving per-channel series of (burst count, occupied seconds).  Bins in which
*no channel at the site* had any burst are treated as sensor-off and dropped.

Usage: python screen_events.py --occ-dir <dir> --out results/ [--bin 10] [--thr -70]
"""
import argparse, glob, os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from screen_channels import acf_at, lomb_scargle_daily, runs

def screen(site, df, bin_min, thr):
    thr_col = str(thr)
    df = df.dropna(subset=[thr_col])          # bursts that reached this threshold
    df["bin"] = df["Time"].dt.floor(f"{bin_min}min")
    agg = df.groupby(["Frequency", "bin"]).agg(n=(thr_col, "size"), occ_s=(thr_col, "sum"),
                                              med_burst=(thr_col, "median"), max_burst=(thr_col, "max"))
    on_bins = pd.Index(sorted(df["bin"].unique()))     # sensor on (any channel active)
    rows = []
    for f in sorted(df.Frequency.unique()):
        a = agg.loc[f].reindex(on_bins).fillna({"n": 0, "occ_s": 0})
        n = a["n"].to_numpy(); occ = a["occ_s"].to_numpy()
        active = n > 0
        p = active.mean()
        ent = 0.0 if p in (0, 1) else -(p*np.log2(p) + (1-p)*np.log2(1-p))
        rb, ri = runs(active)
        s = pd.Series(occ, index=on_bins).resample("1h").sum(min_count=1)
        hod = s.groupby(s.index.hour).mean()
        valid = s.dropna()
        if len(valid) > 48 and valid.std() > 0:
            pred = valid.index.hour.map(hod)
            r2 = 1 - ((valid.to_numpy() - pred.to_numpy())**2).sum() / ((valid - valid.mean())**2).sum()
        else:
            r2 = np.nan
        t_h = (s.index - s.index[0]).total_seconds().to_numpy()/3600
        ls24, ls12 = lomb_scargle_daily(t_h, s.to_numpy())
        bursts = df[df.Frequency == f][thr_col]
        rows.append(dict(site=site, freq_MHz=round(f, 1), thr_dBm=thr,
            on_hours=round(len(on_bins)*bin_min/60, 1), span_days=round((on_bins[-1]-on_bins[0]).total_seconds()/86400, 1),
            n_bursts=int(n.sum()), burst_med_ms=round(bursts.median()*1e3, 2), burst_p90_ms=round(bursts.quantile(.9)*1e3, 2),
            burst_max_ms=round(bursts.max()*1e3, 1),
            p_active=round(p, 3), state_entropy=round(ent, 3),
            mean_active_run_min=round(rb.mean()*bin_min, 1) if len(rb) else np.nan,
            mean_quiet_run_min=round(ri.mean()*bin_min, 1) if len(ri) else np.nan,
            n_transitions=int(len(rb)+len(ri)-1) if len(rb)+len(ri) else 0,
            acf_24h=round(acf_at(s, 24), 3), acf_1h=round(acf_at(s, 1), 3),
            r2_hour_of_day=round(r2, 3), ls_24h=round(ls24, 1), ls_12h=round(ls12, 1),
            hod_peak=int(hod.idxmax()), hod_trough=int(hod.idxmin())))
    return pd.DataFrame(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--occ-dir", required=True); ap.add_argument("--out", default="results")
    ap.add_argument("--bin", type=int, default=10); ap.add_argument("--thr", type=int, default=-70)
    ap.add_argument("--sites", nargs="*")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    allr = []
    for p in sorted(glob.glob(os.path.join(a.occ_dir, "*.csv.gz"))):
        site = os.path.basename(p).split(".")[0]
        if a.sites and site not in a.sites: continue
        print(f"[{site}] {p}", file=sys.stderr)
        df = pd.read_csv(p); df["Time"] = pd.to_datetime(df["Time"])
        r = screen(site, df, a.bin, a.thr); r.to_csv(os.path.join(a.out, f"events_{site}_{a.thr}.csv"), index=False); allr.append(r)
    full = pd.concat(allr, ignore_index=True)
    full["score"] = full.state_entropy * (0.5 + full.acf_24h.clip(lower=0).fillna(0) + full.r2_hour_of_day.clip(lower=0).fillna(0)) * np.log1p(full.on_hours)/np.log1p(24*14)
    full = full.sort_values("score", ascending=False)
    full.to_csv(os.path.join(a.out, f"events_all_{a.thr}.csv"), index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
    print(full.to_string(index=False))

if __name__ == "__main__":
    main()
