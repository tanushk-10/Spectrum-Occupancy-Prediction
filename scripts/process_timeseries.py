"""Stream NIST denoised time-series archives into per-look Parquet files."""

import argparse
import io
import os
import tarfile

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


THRESHOLDS_DBM = (-75, -70, -65, -60, -55)
INDEX_COLUMNS = ("Time", "Frequency", "Sweep")


class _TarMemberReader(io.RawIOBase):
    def __init__(self, stream):
        self.stream = stream

    def readable(self):
        return True

    def readinto(self, buffer):
        chunk = self.stream.read(len(buffer))
        size = len(chunk)
        buffer[:size] = chunk
        return size

    def close(self):
        if not self.closed:
            self.stream.close()
        super().close()


def summarize_look_chunk(frame, site):
    """Convert one input chunk of sensor looks to the requested output schema."""
    if tuple(frame.columns[:3]) != INDEX_COLUMNS:
        raise ValueError(f"Expected first columns {INDEX_COLUMNS}, got {tuple(frame.columns[:3])}")
    if len(frame.columns) < 4:
        raise ValueError("Expected at least one power sample column")

    powers = frame.iloc[:, 3:].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
    finite = np.isfinite(powers)
    positive = finite & (powers > 0)
    n_samples = finite.sum(axis=1)
    n_positive = positive.sum(axis=1)
    positive_power = np.where(positive, powers, 0.0)
    has_samples = n_samples > 0
    has_positive = n_positive > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        sample_dbm = 10.0 * np.log10(np.where(positive, powers, np.nan))
        max_dbm = np.max(np.where(positive, sample_dbm, -np.inf), axis=1)
        mean_mw = positive_power.sum(axis=1) / np.maximum(n_positive, 1)
        mean_dbm = 10.0 * np.log10(mean_mw)

    result = pd.DataFrame({
        "site": site,
        "freq_MHz": pd.to_numeric(frame["Frequency"], errors="raise").to_numpy(dtype=np.float64),
        "time": pd.to_datetime(frame["Time"], errors="raise"),
        "sweep": pd.to_numeric(frame["Sweep"], errors="raise").to_numpy(dtype=np.int64),
        "n_samples": n_samples.astype(np.int64),
    })
    result["time"] = result["time"].to_numpy(dtype="datetime64[ns]")
    for threshold in THRESHOLDS_DBM:
        above = np.sum(positive & (sample_dbm >= threshold), axis=1)
        result[f"frac_{threshold}"] = np.divide(
            above,
            n_samples,
            out=np.full(len(frame), np.nan, dtype=np.float64),
            where=has_samples,
        )
    result["max_dBm"] = np.where(has_positive, max_dbm, np.nan)
    result["mean_dBm"] = np.where(has_positive, mean_dbm, np.nan)
    return result


def process_archive(archive_path, site, output_path, chunksize=50_000):
    """Read CSV members sequentially from a gzip tar archive and write Parquet."""
    if chunksize < 1:
        raise ValueError("chunksize must be positive")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    writer = None
    rows_written = 0
    member_count = 0
    try:
        with tarfile.open(archive_path, mode="r|gz") as archive:
            for member in archive:
                if not member.isfile() or not member.name.lower().endswith(".csv"):
                    continue
                member_count += 1
                stream = archive.extractfile(member)
                if stream is None:
                    raise OSError(f"Could not read archive member {member.name}")
                print(f"[{site}] streaming {member.name}")
                with io.BufferedReader(_TarMemberReader(stream)) as csv_stream:
                    for frame in pd.read_csv(csv_stream, chunksize=chunksize):
                        looks = summarize_look_chunk(frame, site)
                        table = pa.Table.from_pandas(looks, preserve_index=False)
                        if writer is None:
                            writer = pq.ParquetWriter(output_path, table.schema, compression="zstd")
                        writer.write_table(table)
                        rows_written += len(looks)
    finally:
        if writer is not None:
            writer.close()
    if member_count == 0:
        raise ValueError(f"No CSV members found in {archive_path}")
    if rows_written == 0:
        raise ValueError(f"No data rows found in {archive_path}")
    print(f"[{site}] wrote {rows_written:,} looks from {member_count} CSV members to {output_path}")
    return rows_written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, help="NIST site .tar.gz archive")
    parser.add_argument("--site", required=True, help="Two-digit site identifier")
    parser.add_argument("--output", required=True, help="Output Parquet path")
    parser.add_argument("--chunksize", type=int, default=50_000, help="CSV rows per processing chunk")
    args = parser.parse_args()
    process_archive(args.archive, args.site, args.output, args.chunksize)


if __name__ == "__main__":
    main()