# Example analysis: cohort representation and overlap

Scientific question: how does population representation change between the
Phase 3 cohort and the expanded cohort, and can they be treated as independent
sets of participants?

Requires Python 3 and hydrated `subject.tsv`, `sample.tsv`, `sample_set.tsv`,
and `population_descriptor.tsv`. No packages or payload downloads are needed
once these metadata tables are available.

From `attic/ANVIL_1000G_PRIMED_data_model`:

```bash
python3 scripts/analyze_cohorts.py > cohort_analysis.md
python3 -m unittest discover -s scripts -v
```

The script prints a Markdown report with unique-subject overlap, population
and superpopulation counts, reported-sex composition, and changes in cohort
shares. It resolves inputs relative to the script, so it also works from other
working directories. Use `--data-dir` for another copy of these tables.

Compare other sample sets using their exact IDs:

```bash
python3 scripts/analyze_cohorts.py \
  --baseline AFR_phase3_unrelated --target AFR_highcov_unrelated
```

The default comparison contains 2,504 baseline and 3,202 target subjects:
2,504 shared, 698 added, and none removed. Thus these are overlapping cohorts,
not independent replication sets. Population share changes identify where
the expansion changes representation; they do not demonstrate genetic or
clinical effects. A sample-set name containing `unrelated` is a supplied label,
not a kinship assessment performed by this script.

The other inspected TSVs describe sequencing datasets and file locations;
`plink_file_wide.tsv` points to PLINK files rather than containing genotypes.
Genetic association or allele-frequency analyses would require those actual
genotype payloads and appropriate phenotype/QC information.

## Discover authentication requirements

See [DISCOVER_README.md](DISCOVER_README.md) for the discovery script's usage,
input requirements, JSON output, authentication gaps, and offline checks.
