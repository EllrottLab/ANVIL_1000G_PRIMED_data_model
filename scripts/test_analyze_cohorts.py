"""Run with: python3 -m unittest discover -s scripts -v (from the data directory)."""

import tempfile
import unittest
from pathlib import Path

from analyze_cohorts import compare, load_cohorts, report


class CohortAnalysisTest(unittest.TestCase):
    def test_join_deduplication_changes_and_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            tables = {
                "subject": "subject_id\treported_sex\na\tFemale\nb\tMale\nc\tUnknown\n",
                "sample": "sample_id\tsubject_id\ns1\ta\ns2\ta\ns3\tb\ns4\tc\n",
                "population_descriptor": (
                    "subject_id\tpopulation_descriptor\tpopulation_label\n"
                    "a\tpopulation | superpopulation\tP1 | S1\n"
                    "b\tsuperpopulation | population\tS1 | P2\n"
                    "c\tpopulation | superpopulation\tP2 | S1\n"
                ),
                "sample_set": (
                    "sample_set_id\tsample_id\nold\ts1\nold\ts2\nold\ts1\nold\ts3\n"
                    "new\ts2\nnew\ts4\n"
                ),
            }
            for name, content in tables.items():
                (directory / f"{name}.tsv").write_text(content)
            subjects, cohorts = load_cohorts(directory)
            self.assertEqual(cohorts, {"old": {"a", "b"}, "new": {"a", "c"}})
            self.assertEqual(compare(subjects, cohorts["old"], cohorts["new"], "population"),
                             [("P1", 1, 1, 0, 0, 0.0), ("P2", 1, 1, 1, 1, 0.0)])
            self.assertEqual(compare(subjects, {"a", "b"}, {"a"}, "population")[0][-1], 50.0)
            self.assertIn("Shared: 1; added: 1; removed: 1", report(subjects, cohorts, "old", "new"))
            with self.assertRaisesRegex(ValueError, "Unknown or empty"):
                report(subjects, cohorts, "absent", "new")
            path = directory / "sample_set.tsv"
            path.write_text(tables["sample_set"] + "new\tmissing\n")
            with self.assertRaisesRegex(ValueError, "Unknown sample"):
                load_cohorts(directory)
            path.write_text("version https://calypr.github.io/spec/v1\n")
            with self.assertRaisesRegex(ValueError, "hydrate DRS pointers"):
                load_cohorts(directory)
            path.write_text("sample_set_id\tsample_id\nnew\n")
            with self.assertRaisesRegex(ValueError, "malformed row"):
                load_cohorts(directory)


if __name__ == "__main__":
    unittest.main()
