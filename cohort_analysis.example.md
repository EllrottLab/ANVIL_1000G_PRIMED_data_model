# Cohort representation analysis

Baseline: `phase3_2504_samples`; target: `all_3202_samples`.

- Unique subjects: 2,504 → 3,202 (+27.9%).
- Shared: 2,504; added: 698; removed: 0.
- Unique subjects across both cohorts: 3,202. Adding the cohort sizes would double-count shared subjects.

## Superpopulation

| Label | Baseline n | Target n | Added | Removed | Share change (pp) |
| --- | ---: | ---: | ---: | ---: | ---: |
| AFR | 661 | 893 | 232 | 0 | +1.49 |
| AMR | 347 | 490 | 143 | 0 | +1.45 |
| EAS | 504 | 585 | 81 | 0 | -1.86 |
| EUR | 503 | 633 | 130 | 0 | -0.32 |
| SAS | 489 | 601 | 112 | 0 | -0.76 |

## Population

| Label | Baseline n | Target n | Added | Removed | Share change (pp) |
| --- | ---: | ---: | ---: | ---: | ---: |
| ACB | 96 | 116 | 20 | 0 | -0.21 |
| ASW | 61 | 74 | 13 | 0 | -0.13 |
| BEB | 86 | 131 | 45 | 0 | +0.66 |
| CDX | 93 | 93 | 0 | 0 | -0.81 |
| CEU | 99 | 179 | 80 | 0 | +1.64 |
| CHB | 103 | 103 | 0 | 0 | -0.90 |
| CHS | 105 | 163 | 58 | 0 | +0.90 |
| CLM | 94 | 132 | 38 | 0 | +0.37 |
| ESN | 99 | 149 | 50 | 0 | +0.70 |
| FIN | 99 | 99 | 0 | 0 | -0.86 |
| GBR | 91 | 91 | 0 | 0 | -0.79 |
| GIH | 103 | 103 | 0 | 0 | -0.90 |
| GWD | 113 | 178 | 65 | 0 | +1.05 |
| IBS | 107 | 157 | 50 | 0 | +0.63 |
| ITU | 102 | 107 | 5 | 0 | -0.73 |
| JPT | 104 | 104 | 0 | 0 | -0.91 |
| KHV | 99 | 122 | 23 | 0 | -0.14 |
| LWK | 99 | 99 | 0 | 0 | -0.86 |
| MSL | 85 | 99 | 14 | 0 | -0.30 |
| MXL | 64 | 97 | 33 | 0 | +0.47 |
| PEL | 85 | 122 | 37 | 0 | +0.42 |
| PJL | 96 | 146 | 50 | 0 | +0.73 |
| PUR | 104 | 139 | 35 | 0 | +0.19 |
| STU | 102 | 114 | 12 | 0 | -0.51 |
| TSI | 107 | 107 | 0 | 0 | -0.93 |
| YRI | 108 | 178 | 70 | 0 | +1.25 |

## Reported Sex

| Label | Baseline n | Target n | Added | Removed | Share change (pp) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Female | 1271 | 1603 | 332 | 0 | -0.70 |
| Male | 1233 | 1599 | 366 | 0 | +0.70 |

## Interpretation

The largest absolute population share change is CEU (+1.64 percentage points). Share changes distinguish shifts in cohort composition from simple growth in sample count.

Overlapping cohorts are not independent replication samples. Use the subject intersection to prevent train/test leakage or duplicate inclusion.

## Methods and limits

Joined sample_set → sample → subject and population_descriptor by their explicit IDs. Repeated memberships and multiple samples from one subject count once per cohort. Share change = 100 × (target group n / target N − baseline group n / baseline N).

Population labels are supplied metadata, not genetically inferred ancestry. Reported sex is summarized as recorded. Missing joins or malformed required fields fail explicitly.

These TSVs do not contain genotypes, phenotypes, or pedigree relationships. This analysis cannot establish allele-frequency differences, disease associations, genetic independence, or statistical power. No hypothesis tests are applied to these overlapping cohorts.

