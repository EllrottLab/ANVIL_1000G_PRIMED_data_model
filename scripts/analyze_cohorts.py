#!/usr/bin/env python3
"""Compare cohort representation using hydrated TSV metadata; Python stdlib only."""

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def read_table(directory, name, columns):
    path = directory / f"{name}.tsv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not set(columns) <= set(reader.fieldnames or []):
            raise ValueError(f"{path}: missing columns {columns}; hydrate DRS pointers first")
        rows = list(reader)
    for line, row in enumerate(rows, 2):
        if None in row or any(not (row.get(column) or "").strip() for column in columns):
            raise ValueError(f"{path}:{line}: malformed row or empty required value")
    return rows


def index(rows, key):
    result = {}
    for row in rows:
        if row[key] in result:
            raise ValueError(f"Duplicate {key}: {row[key]}")
        result[row[key]] = row
    return result


def load_cohorts(directory):
    subjects = index(read_table(directory, "subject", ["subject_id", "reported_sex"]), "subject_id")
    samples = index(read_table(directory, "sample", ["sample_id", "subject_id"]), "sample_id")
    populations = index(read_table(directory, "population_descriptor", [
        "subject_id", "population_descriptor", "population_label",
    ]), "subject_id")
    for subject_id, subject in subjects.items():
        if subject_id not in populations:
            raise ValueError(f"Missing population descriptor for {subject_id}")
        row = populations[subject_id]
        keys = [value.strip() for value in row["population_descriptor"].split("|")]
        values = [value.strip() for value in row["population_label"].split("|")]
        if (len(keys) != len(values) or len(set(keys)) != len(keys)
                or not all(values) or not {"population", "superpopulation"} <= set(keys)):
            raise ValueError(f"Invalid population descriptor for {subject_id}")
        subject.update(zip(keys, values))
    for sample in samples.values():
        if sample["subject_id"] not in subjects:
            raise ValueError(f"Unknown subject: {sample['subject_id']}")
    cohorts = defaultdict(set)
    for row in read_table(directory, "sample_set", ["sample_set_id", "sample_id"]):
        if row["sample_id"] not in samples:
            raise ValueError(f"Unknown sample: {row['sample_id']}")
        cohorts[row["sample_set_id"]].add(samples[row["sample_id"]]["subject_id"])
    return subjects, cohorts


def compare(subjects, baseline, target, field):
    before = Counter(subjects[s][field] for s in baseline)
    after = Counter(subjects[s][field] for s in target)
    added = Counter(subjects[s][field] for s in target - baseline)
    removed = Counter(subjects[s][field] for s in baseline - target)
    return [
        (label, before[label], after[label], added[label], removed[label],
         100 * (after[label] / len(target) - before[label] / len(baseline)))
        for label in sorted(before.keys() | after.keys())
    ]


def report(subjects, cohorts, baseline_name, target_name):
    for name in (baseline_name, target_name):
        if name not in cohorts or not cohorts[name]:
            raise ValueError(f"Unknown or empty sample set: {name}")
    baseline, target = cohorts[baseline_name], cohorts[target_name]
    lines = [
        "# Cohort representation analysis", "",
        f"Baseline: `{baseline_name}`; target: `{target_name}`.", "",
        f"- Unique subjects: {len(baseline):,} → {len(target):,} "
        f"({100 * (len(target) / len(baseline) - 1):+.1f}%).",
        f"- Shared: {len(baseline & target):,}; added: {len(target - baseline):,}; "
        f"removed: {len(baseline - target):,}.",
        f"- Unique subjects across both cohorts: {len(baseline | target):,}. "
        "Adding the cohort sizes would double-count shared subjects.", "",
    ]
    for field in ("superpopulation", "population", "reported_sex"):
        lines += [f"## {field.replace('_', ' ').title()}", "",
                  "| Label | Baseline n | Target n | Added | Removed | Share change (pp) |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for label, before, after, added, removed, shift in compare(subjects, baseline, target, field):
            lines.append(f"| {label} | {before} | {after} | {added} | {removed} | {shift:+.2f} |")
        lines.append("")
    changes = compare(subjects, baseline, target, "population")
    largest = max(changes, key=lambda row: abs(row[5]))
    lines += [
        "## Interpretation", "",
        f"The largest absolute population share change is {largest[0]} "
        f"({largest[5]:+.2f} percentage points). "
        "Share changes distinguish shifts in cohort composition from simple growth in sample count.", "",
        "Overlapping cohorts are not independent replication samples. "
        "Use the subject intersection to prevent train/test leakage or duplicate inclusion.", "",
        "## Methods and limits", "",
        "Joined sample_set → sample → subject and population_descriptor by their explicit IDs. "
        "Repeated memberships and multiple samples from one subject count once per cohort. "
        "Share change = 100 × (target group n / target N − baseline group n / baseline N).", "",
        "Population labels are supplied metadata, not genetically inferred ancestry. "
        "Reported sex is summarized as recorded. Missing joins or malformed required fields fail explicitly.", "",
        "These TSVs do not contain genotypes, phenotypes, or pedigree relationships. "
        "This analysis cannot establish allele-frequency differences, disease associations, "
        "genetic independence, or statistical power. No hypothesis tests are applied to these overlapping cohorts.", "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline", default="phase3_2504_samples")
    parser.add_argument("--target", default="all_3202_samples")
    args = parser.parse_args()
    try:
        subjects, cohorts = load_cohorts(args.data_dir)
        print(report(subjects, cohorts, args.baseline, args.target))
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
