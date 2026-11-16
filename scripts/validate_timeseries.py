"""Summarize per-look Parquet data and compare it with NIST occupancy durations."""

import argparse
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


SAMPLE_PERIOD_SECONDS = 0.0005
SAMPLES_PER_LOOK = 210


def load_look_stats(path):
    counts = Counter()
    sample_counts = Counter()
    channel_sample_counts = defaultdict(Counter)
    times = defaultdict(list)
    busy_samples = Counter()
    finite_samples = Counter()
    all_times = []
    order_groups = defaultdict(list)
    order_rows_seen = 0
    total_rows = 0

    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(
        columns=["freq_MHz", "time", "sweep", "n_samples", "frac_-70"],
        batch_size=250_000,
    ):
        frame = batch.to_pandas()
        total_rows += len(frame)
        frame["freq_MHz"] = frame["freq_MHz"].round(1)
        timestamp_ns = frame["time"].to_numpy(dtype="datetime64[ns]").astype(np.int64)
        all_times.append(timestamp_ns)
        for frequency, positions in frame.groupby("freq_MHz", sort=False).indices.items():
            rows = frame.iloc[positions]
            counts[frequency] += len(rows)
            samples = rows["n_samples"].to_numpy(dtype=np.int64)
            sample_counts.update(Counter(samples.tolist()))
            channel_sample_counts[frequency].update(Counter(samples.tolist()))
            finite_samples[frequency] += int(samples.sum())
            busy = (rows["frac_-70"].fillna(0).to_numpy() * samples).sum()
            busy_samples[frequency] += float(busy)
            times[frequency].extend(timestamp_ns[positions].tolist())

        if order_rows_seen < 20_000:
            sample = frame.iloc[: 20_000 - order_rows_seen].copy()
            order_rows_seen += len(sample)
            sample["date"] = sample["time"].dt.date
            for key, group in sample.groupby(["date", "sweep"], sort=False):
                order_groups[key].extend(zip(group["time"].astype("int64"), group["freq_MHz"]))

    complete_orders = set()
    complete_sweeps = 0
    for rows in order_groups.values():
        if len(rows) == 21 and len({frequency for _, frequency in rows}) == 21:
            signature = tuple(frequency for _, frequency in sorted(rows))
            complete_orders.add(signature)
            complete_sweeps += 1
    return {
        "counts": counts,
        "sample_counts": sample_counts,
        "channel_sample_counts": channel_sample_counts,
        "times": times,
        "busy_samples": busy_samples,
        "finite_samples": finite_samples,
        "all_times": np.sort(np.concatenate(all_times)) if all_times else np.array([], dtype=np.int64),
        "orders": complete_orders,
        "complete_sweeps": complete_sweeps,
        "total_rows": total_rows,
    }


def load_duration_totals(path):
    frame = pd.read_csv(path, compression="gzip", usecols=["Frequency", "-70"])
    frame["Frequency"] = pd.to_numeric(frame["Frequency"]).round(1)
    frame["-70"] = pd.to_numeric(frame["-70"], errors="coerce")
    return frame.groupby("Frequency")["-70"].agg(["count", "sum"])


def seconds_between(first_ns, second_ns):
    return pd.Timestamp(first_ns).strftime("%Y-%m-%d %H:%M:%S"), pd.Timestamp(second_ns).strftime("%Y-%m-%d %H:%M:%S")


def percent(value):
    return f"{100 * value:.2f}%" if np.isfinite(value) else "not listed"


def duration_text(seconds):
    if seconds >= 86_400:
        return f"{seconds / 86_400:.1f} days"
    if seconds >= 3_600:
        return f"{seconds / 3_600:.1f} hours"
    if seconds >= 60:
        return f"{seconds / 60:.1f} minutes"
    return f"{seconds:.1f} seconds"


def site_report(site, looks_path, occupancy_path):
    stats = load_look_stats(looks_path)
    durations = load_duration_totals(occupancy_path)
    lines = [f"## Site {site}", "", f"- Sensor looks: {stats['total_rows']:,}"]
    if stats["all_times"].size:
        lines.append(
            f"- Dates covered: {pd.Timestamp(stats['all_times'][0]).date()} to "
            f"{pd.Timestamp(stats['all_times'][-1]).date()}"
        )
    lines.append(f"- Channels: {len(stats['counts'])}")
    sample_hist = stats["sample_counts"]
    if len(sample_hist) == 1:
        only_samples, only_count = next(iter(sample_hist.items()))
        sample_summary = f"{only_samples} in every look ({only_count:,} looks)"
    else:
        sample_summary = ", ".join(
            f"{n} in {count:,} looks" for n, count in sorted(sample_hist.items())
        )
    lines.append(f"- Samples per look: {sample_summary}")
    median_intervals = []
    for timestamps in stats["times"].values():
        gaps = np.diff(np.sort(np.asarray(timestamps, dtype=np.int64))) / 1e9
        if len(gaps):
            median_intervals.append(float(np.median(gaps)))
    if median_intervals:
        lines.append(f"- Typical time between looks on a channel: {np.median(median_intervals):.1f} seconds")
    if stats["complete_sweeps"] and len(stats["orders"]) == stats["complete_sweeps"]:
        order_summary = (
            f"I found a different channel order in each of "
            f"{stats['complete_sweeps']:,} complete sweeps I checked."
        )
    elif stats["complete_sweeps"] > 1 and len(stats["orders"]) == 1:
        order_summary = (
            f"I found the same channel order in all {stats['complete_sweeps']:,} "
            "complete sweeps I checked."
        )
    else:
        order_summary = (
            f"I found {len(stats['orders'])} different channel orders in "
            f"{stats['complete_sweeps']:,} complete sweeps I checked."
        )
    lines.append(f"- {order_summary}")
    lines.extend([
        "",
        "| Channel (MHz) | Looks | Readings above -70 dBm | Typical revisit | Gaps over 1 min | Duration-based -70 dBm estimate |",
        "|---:|---:|---:|---:|---:|---:|",
    ])

    for frequency in sorted(stats["counts"]):
        timestamps = np.sort(np.asarray(stats["times"][frequency], dtype=np.int64))
        gaps = np.diff(timestamps) / 1e9
        median_gap = float(np.median(gaps)) if len(gaps) else np.nan
        long_gaps = gaps[gaps > 60]

        n_samples = stats["finite_samples"][frequency]
        occupancy = stats["busy_samples"][frequency] / n_samples if n_samples else np.nan
        duration_frequency = min(durations.index, key=lambda value: abs(value - frequency)) if len(durations) else None
        duration_row = (
            durations.loc[duration_frequency]
            if duration_frequency is not None and abs(duration_frequency - frequency) <= 5.1
            else None
        )
        sampled_seconds = n_samples * SAMPLE_PERIOD_SECONDS
        duration_rate = (
            float(duration_row["sum"]) / sampled_seconds
            if duration_row is not None and sampled_seconds
            else np.nan
        )
        lines.append(
            f"| {frequency:g} | {stats['counts'][frequency]:,} | {percent(occupancy)} | "
            f"{median_gap:.1f} s | {len(long_gaps):,} | {percent(duration_rate)} |"
        )

    site_outages = []
    if stats["all_times"].size > 1:
        site_gaps = np.diff(stats["all_times"]) / 1e9
        for gap_index in np.flatnonzero(site_gaps > 120):
            before, after = seconds_between(stats["all_times"][gap_index], stats["all_times"][gap_index + 1])
            site_outages.append((site_gaps[gap_index], before, after))
    lines.extend(["", "### Site-wide gaps over 2 minutes"])
    if site_outages:
        for seconds, before, after in sorted(site_outages, reverse=True)[:5]:
            lines.append(f"- {before} to {after}: {duration_text(seconds)} without recorded looks")
    else:
        lines.append("- None found.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--looks-dir", default="results")
    parser.add_argument("--occ-dir", default="data/occ")
    parser.add_argument("--output", default="results/per_look_validation.md")
    args = parser.parse_args()
    reports = [
        "# My per-look data summary",
        "",
        "A look is one brief measurement on one channel. I processed the NIST readings "
        "for sites 02 and 12 and summarized channel coverage, how often the sensor "
        "returned to each channel, long gaps, and readings above -70 dBm.",
        "",
        "Each look normally contains 210 power readings. I count zero and negative "
        "readings as below the threshold and leave missing readings out. For mean and "
        "maximum signal strength in dBm, I use positive readings only and average the "
        "power in mW before converting the mean to dBm.",
        "",
        "I also checked channel order in the first 20,000 looks. To compare occupancy, "
        "I added up the -70 dBm burst durations in NIST's event file and divided by "
        "sampled time. I matched channel labels to the nearest event-file frequency "
        "within 5.1 MHz. `Not listed` means NIST's event file has no burst rows for "
        "that channel; it does not mean measured occupancy was zero. The two percentages "
        "can differ because the methods measure activity in different ways.",
        "",
    ]
    for site in ("02", "12"):
        looks = f"{args.looks_dir}/looks_{site}.parquet"
        occupancy = f"{args.occ_dir}/{site}.csv.gz"
        reports.append(site_report(site, looks, occupancy))
    with open(args.output, "w", encoding="utf-8", newline="\n") as output:
        output.write("\n".join(reports))
    print(f"Wrote {args.output}")