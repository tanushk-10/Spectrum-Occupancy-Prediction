import io
import os
import tarfile
import tempfile
import unittest

import numpy as np
import pandas as pd

from scripts.process_timeseries import process_archive


class ProcessTimeseriesTests(unittest.TestCase):
    def test_streams_members_and_summarizes_valid_power(self):
        with tempfile.TemporaryDirectory() as work:
            archive_path = os.path.join(work, "tiny.tar.gz")
            members = {
                "first.csv": (
                    "Time,Frequency,Sweep,a,b,c,d,e\n"
                    "2020-06-15 00:00:00,100,1,1e-8,1,100,0,-1\n"
                    "2020-06-15 00:00:10,200,1,NaN,0,-2,,NaN\n"
                ),
                "second.csv": (
                    "Time,Frequency,Sweep,a,b\n"
                    "2020-06-15 00:00:20,100,2,1e-8,\n"
                ),
            }
            with tarfile.open(archive_path, "w:gz") as archive:
                for name, text in members.items():
                    payload = text.encode("utf-8")
                    info = tarfile.TarInfo(name)
                    info.size = len(payload)
                    archive.addfile(info, io.BytesIO(payload))

            output_path = os.path.join(work, "looks.parquet")
            written = process_archive(archive_path, "02", output_path, chunksize=1)
            looks = pd.read_parquet(output_path)

        self.assertEqual(written, 3)
        self.assertEqual(list(looks.columns), [
            "site", "freq_MHz", "time", "sweep", "n_samples",
            "frac_-75", "frac_-70", "frac_-65", "frac_-60", "frac_-55",
            "max_dBm", "mean_dBm",
        ])
        self.assertEqual(looks.loc[0, "n_samples"], 5)
        self.assertAlmostEqual(looks.loc[0, "frac_-70"], 2 / 5)
        self.assertEqual(looks.loc[0, "max_dBm"], 20)
        self.assertAlmostEqual(
            looks.loc[0, "mean_dBm"], 10 * np.log10((1e-8 + 1 + 100) / 3)
        )
        self.assertEqual(looks.loc[1, "n_samples"], 2)
        self.assertTrue(np.isnan(looks.loc[1, "mean_dBm"]))
        self.assertEqual(looks.loc[1, "frac_-70"], 0)
        self.assertEqual(looks.loc[2, "n_samples"], 1)
        self.assertAlmostEqual(looks.loc[2, "max_dBm"], -80)
        self.assertAlmostEqual(looks.loc[2, "frac_-75"], 0)


if __name__ == "__main__":
    unittest.main()