# ANVIL 1000G PRIMED Data Model Repository

This repository demonstrates **version-controlled dataset layouts without copying controlled-access payloads into Git**. Using **git-drs**, we manage genomic data model files from the ANVIL project with DRS pointers that enable secure, authorization-independent data access.

## Overview

The ANVIL_1000G_PRIMED_data_model repository is a reference proof-of-concept that shows:

- **Git moves references. ANVIL moves bytes.** 
  - Repository contains only portable DRS URI pointers, not payload data
  - Each user authenticates independently to ANVIL for data access
  - No credentials, signed URLs, or provider-specific tokens in Git

- **Four perspectives on one reference model:**
  1. **Data reference author** - Publish reviewable, versioned dataset layouts without downloading payloads
  2. **Data consumer** - Clone pointers, authenticate independently, hydrate everything or only matching patterns
  3. **Unauthorized reader** - Inspect repository history but cannot access controlled data without authorization
  4. **Repository maintainer** - Review deterministic pointers and diagnose provider issues

### Data Files Included

The repository tracks the following TSV (Tab-Separated Values) data model files as DRS pointers:

- **sequencing_dataset.tsv** - Sequencing dataset metadata
- **subject.tsv** - Subject/individual information
- **sample.tsv** - Biosampling metadata
- **sample_set.tsv** - Groups of samples
- **population_descriptor.tsv** - Population descriptors and ancestry information
- **sequencing_file.tsv** - Information about individual sequencing files
- **plink_file_wide.tsv** - PLINK format genetic data

These files describe the structure and relationships of genomic samples and datasets from the 1000 Genomes Project PRIMED (Population Reference Integration with Metadata and Expression Data) initiative.

## Key Concepts: The Zero-Payload Model

### What Are DRS Pointers?

Instead of storing large data files in Git, this repository stores **portable DRS pointers** that reference data in ANVIL:

```
version https://calypr.github.io/spec/v1
oid drs://authority/object-id
size 987654321
sha256 8d969eef…
```

**Benefits:**
- ✅ Small Git repository (only metadata and pointers)
- ✅ Version control for data layouts and structure
- ✅ No payload bytes, tokens, or credentials in Git
- ✅ Each user authenticates independently for access
- ✅ Works with authorization controls at the DRS provider level

### Security Boundary

Git visibility reveals file paths and DRS identifiers, but **never grants authorization to underlying data**. This means:
- Unauthorized readers can clone the repo and see file structure
- They receive a clear denial when attempting to hydrate controlled data
- Each user supplies their own ANVIL credentials independently
- No credentials, tokens, or signed URLs are stored in Git

## Prerequisites

Before you begin, ensure you have:

1. **git-drs installed**
   ```bash
   git drs install
   ```
   Follow the full installation at https://github.com/calypr/git-drs

2. **Git** (version 2.9 or later)

3. **Google Cloud SDK with ADC**
   ```bash
   gcloud auth application-default login
   ```
   This enables git-drs to request fresh access tokens from ANVIL/Terra

4. **ANVIL Account**
   - Sign up at https://www.anvilproject.org
   - Access to ANVIL Data Explorer at https://explore.anvilproject.org
   - Required for both authors (adding references) and consumers (hydrating data)

5. **Optional: GitHub Account**
   - For publishing repositories to GitHub
   - Not required if staying local

## How to Recreate This Repository

This workflow follows the git-drs zero-payload pattern: **add once, publish with ordinary Git, configure per clone**.

### Phase 1: Create and Populate (Data Reference Author)

#### Step 1: Initialize and Configure

```bash
# Set up Google Cloud authentication
gcloud auth application-default login

# Create and initialize repository
mkdir my-anvil-repo
cd my-anvil-repo
git init
git drs init

# Configure the Terra remote (author-side, only in local .git/config)
git drs remote add anvil terra
```

#### Step 2: Access ANVIL Data Explorer and Download Manifest

1. Navigate to [ANVIL Data Explorer](https://explore.anvilproject.org/files?filter=%5B%7B%22categoryKey%22%3A%22files.file_format%22%2C%22value%22%3A%5B%22.tsv%22%2C%22.tsv.gz%22%5D%7D%2C%7B%22categoryKey%22%3A%22datasets.title%22%2C%22value%22%3A%5B%22ANVIL_1000G_PRIMED_data_model%22%5D%7D%5D)
2. Select the dataset: **ANVIL_1000G_PRIMED_data_model**
3. Filter by file format: **.tsv** files
4. Download the manifest TSV (this contains all file metadata including DRS URIs)

#### Step 3: Add References and Validate

```bash
# Generate git-drs add-ref commands from the manifest
manifest=/tmp/anvil-manifest-38dc7537.tsv
scripts/anvil-add-ref-commands.sh "$manifest" > /tmp/add-anvil-refs.sh

# Review the commands before executing
cat /tmp/add-anvil-refs.sh
git drs add-ref --remote anvil drs://drs.anv0:v2_6d1cf5f0-99a8-3cd9-b580-01102f3abfe7 sequencing_dataset.tsv
git drs add-ref --remote anvil drs://drs.anv0:v2_b6b829f3-6046-3f29-896f-495a23f24c14 subject.tsv
git drs add-ref --remote anvil drs://drs.anv0:v2_093066ee-45f8-3664-9363-c602913ef0c7 sequencing_file.tsv
git drs add-ref --remote anvil drs://drs.anv0:v2_a31c73cb-3bc8-3688-a1e5-05f2d63d0cf9 plink_file_wide.tsv
git drs add-ref --remote anvil drs://drs.anv0:v2_d8add534-63b4-3077-9df5-5ebc8d138415 sample.tsv
git drs add-ref --remote anvil drs://drs.anv0:v2_d6f6836d-688a-33b9-b3d9-f4e829830c0e sample_set.tsv
git drs add-ref --remote anvil drs://drs.anv0:v2_e68887be-c583-375a-a773-48771192c8fa population_descriptor.tsv

# Validate without writing (dry-run)
bash /tmp/add-anvil-refs.sh --dry-run

# Execute to add references as DRS pointers
bash /tmp/add-anvil-refs.sh
```

This populates `.gitattributes` and creates DRS pointer files like:
```
version https://calypr.github.io/spec/v1
oid drs://drs.anv0:v2_6d1cf5f0-99a8-3cd9-b580-01102f3abfe7
size 10384
sha256 76f4ef9e3b8814870583eea92fbf4ba8
```

#### Step 4: Commit and Publish

```bash
# Verify only pointers, not payloads, will be committed
git status

# Commit pointer files
git add .gitattributes '*.tsv'
git commit -m "Add references to ANVIL 1000G PRIMED data model"

# Create a remote repository
git branch -M main
git remote add origin https://github.com/<user>/ANVIL_1000G_PRIMED_data_model.git
git push -u origin main
```

**What's in GitHub:**
- Portable DRS pointers and `.gitattributes`
- File paths and metadata
- Git history and versioning

**What's NOT in GitHub:**
- Payload bytes or cached content
- Tokens, credentials, or ADC files
- Signed download URLs or provider secrets

---

### Phase 2: Clone and Hydrate (Data Consumer)

#### Step 1: Clone Repository

```bash
# Set up authentication
gcloud auth application-default login

# Clone the pointer-only repository
git clone https://github.com/<user>/ANVIL_1000G_PRIMED_data_model.git
cd ANVIL_1000G_PRIMED_data_model
```

At this point, `*.tsv` files are DRS pointers, not actual data.

#### Step 2: Configure Terra Remote (Per Clone)

```bash
# Repository-local remote configuration; not cloned from origin
# This is the key security boundary: every clone must recreate its own config
git drs remote add anvil terra --checkout hydrate
```

This enables git-drs to:
- Resolve DRS URIs via the AnVILResolver
- Request fresh access tokens via Google ADC
- Verify file checksums during download

#### Step 3: Hydrate Files

```bash
# Download all authorized TSV files (fetch metadata and data)
git drs pull -I "*.tsv"

# Or hydrate only a specific subset
git drs pull -I "sample.tsv"
```

**Download invariant:**
1. Fetch current metadata and fresh access token
2. Download to temporary file
3. Verify size and SHA256 checksum
4. Atomically promote to cache
5. Hydrate worktree only after validation passes

#### Step 4: Verify and Use

```bash
# Check that files are now hydrated (actual content, not pointers)
git status
head sample.tsv
```

---

### Key Workflow Properties

| Property | Author | Consumer |
|----------|--------|----------|
| **Credentials** | Google ADC (gcloud login) | Google ADC (gcloud login) |
| **Authorization** | Independent to ANVIL | Independent to ANVIL |
| **Git payload** | Only pointers + metadata | Only pointers + metadata |
| **Hydration** | Optional (for verification) | Required (to access data) |
| **Isolation** | Home, config, cache separate | Home, config, cache separate |

## Working with the Repository

### Listing Tracked Files

```bash
git drs ls-files
```

### Checking File Status

Files in this repository will appear as DRS pointers until hydrated:

```bash
# Before hydration: shows pointer files
git status

# After hydration: shows actual content
git drs pull -I "*.tsv"
git status
```

### Adding New Data Files

To add a new data file to the repository (author workflow):

1. Obtain the DRS URI and metadata from ANVIL Data Explorer
2. Use git-drs to create a reference:
   ```bash
   git drs add-ref --remote anvil drs://drs.anv0:v2_<object-id> data/newfile.tsv
   ```
3. Verify the change:
   ```bash
   git status
   ```
4. Commit and push:
   ```bash
   git add .gitattributes data/
   git commit -m "Add new reference to <file>"
   git push
   ```

## Three Identities, One Reference

git-drs uses three separate identifiers to ensure security and portability:

| Identity | Type | Purpose | Example |
|----------|------|---------|---------|
| **Remote Identity** | DRS URI | Canonical reference stored in Git | `drs://drs.anv0:v2_6d1cf5f0-99a8-3cd9` |
| **Cache OID** | SHA256 | Filesystem-safe key, never replaces remote | `sha256("git-drs-anvil-ref:v1\n" + drs_uri)` |
| **Content SHA256** | SHA256 | Integrity verification during download | Content hash from ANVIL metadata |

**Key principle:** The DRS URI stays canonical and portable. Cache keys and content checksums serve distinct purposes and never override the remote identity.

## Security Architecture

### Authentication Flow

1. **Author perspective:** Adds references with ADC-authorized metadata validation
2. **Git:** Commits only canonical DRS URI, size, and checksum
3. **Consumer perspective:** Clones pointer-only repository, authenticates independently
4. **Hydration:** Requests fresh authorized access URL and verifies bytes

### What Stays Local (Never Published)

- `.git/config` remote configuration
- Credentials (via Google ADC)
- Cached file content
- Temporary files and access tokens
- Signed download URLs

### Acceptance Test Pattern

For independent two-user scenarios:

```bash
# Arrange: Separate homes, configs, ADCs, caches
export HOME=/tmp/user_a
export HOME=/tmp/user_b

# Act: Author commits, consumer clones and authenticates
git drs add-ref --remote anvil <drs-uri> <file>
git commit -m "Add reference"

git clone <repo>
git drs remote add anvil terra --checkout hydrate

# Assert: Verify bytes; check isolated credentials
git drs pull
file <filename>  # verify content, not pointer
```

## ANVIL Data Explorer Integration

### Finding This Dataset

1. Go to [ANVIL Data Explorer](https://explore.anvilproject.org/files?filter=%5B%7B%22categoryKey%22%3A%22files.file_format%22%2C%22value%22%3A%5B%22.tsv%22%2C%22.tsv.gz%22%5D%7D%2C%7B%22categoryKey%22%3A%22datasets.title%22%2C%22value%22%3A%5B%22ANVIL_1000G_PRIMED_data_model%22%5D%7D%5D)
2. Filter by dataset: **ANVIL_1000G_PRIMED_data_model**
3. Filter by file type: **.tsv** (Metadata files)
4. Download the manifest (TSV with DRS URIs and checksums for all files)

### DRS URI Format

Files in this dataset have DRS URIs following the pattern:

```
drs://drs.anv0:v2_<unique-object-identifier>
```

Example from sequencing_dataset.tsv:
```
drs://drs.anv0:v2_6d1cf5f0-99a8-3cd9-b580-01102f3abfe7
```

These URIs are:
- Canonical and stable across versions
- Portable across any GA4GH DRS-compliant client
- Authority for both object metadata and access resolution
- Safely committable to Git without revealing credentials

## Repository Structure

```
ANVIL_1000G_PRIMED_data_model/
├── README.md                           # This file
├── .git/                               # Git repository metadata (shared)
├── .gitattributes                      # DRS filter configuration (shared)
├── sequencing_dataset.tsv              # DRS pointer file (shared, ~10 KB)
├── subject.tsv                         # DRS pointer file (shared, ~80 KB)
├── sample.tsv                          # DRS pointer file (shared, ~76 KB)
├── sample_set.tsv                      # DRS pointer file (shared, ~450 KB)
├── population_descriptor.tsv           # DRS pointer file (shared, ~200 KB)
├── sequencing_file.tsv                 # DRS pointer file (shared, ~1.4 MB)
├── plink_file_wide.tsv                 # DRS pointer file (shared, ~850 KB)
└── etc/                                # Documentation (shared)
    └── anvil-manifest-*.tsv            # ANVIL metadata manifest (reference)
```

**Legend:**
- **(shared)** — Published to GitHub, contains only pointers and metadata
- **DRS pointer file** — Text file referencing ANVIL data (visible in `git diff`, small on disk)
- **Hydrated content** — Downloaded locally after `git drs pull`, stored in cache (not in `.git`)

## Troubleshooting

### Files Appear as Pointer Content Instead of Bytes

This is **correct and expected behavior**. Until you run `git drs pull`, files exist as pointers:

```bash
# Before hydration
cat sample.tsv
# Output: version https://calypr.github.io/spec/v1
#         oid drs://drs.anv0:v2_d8add534-63b4-3077-9df5-5ebc8d138415
#         size 76883
#         sha256 d31b1a54fff9ccc0cb5145b9cf86615c

# After hydration
git drs pull -I "*.tsv"
cat sample.tsv
# Output: (actual TSV content with headers and data rows)
```

### "Permission Denied" or "Unauthorized" During `git drs pull`

This means your Google ADC credentials don't have access to the controlled data:

1. **Verify ADC is configured:**
   ```bash
   gcloud auth application-default print-access-token
   ```
   If this fails, run `gcloud auth application-default login`

2. **Verify you have ANVIL access:**
   - Log in to https://www.anvilproject.org
   - Navigate to the dataset in ANVIL Data Explorer
   - Confirm you can see the data there

3. **Check cached credentials:**
   ```bash
   gcloud auth application-default print-access-token | wc -c
   # If this returns ~1000 characters, ADC is working
   ```

4. **Try a specific file:**
   ```bash
   git drs pull -I "sample.tsv"
   ```

### git-drs Commands Not Found

Ensure git-drs is properly installed:

```bash
git drs --version
```

If not installed, install globally:

```bash
# Clone the repo
git clone https://github.com/calypr/git-drs.git
cd git-drs

# Install
make install
git drs install  # Global filter config
```

### "No remote named 'anvil'" After Cloning

This is expected. Remote configuration is **not cloned**; it's stored only in `.git/config` locally:

```bash
# After cloning, recreate the remote:
git drs remote add anvil terra --checkout hydrate

# Or check what remotes exist:
git drs remote list
```

### Repository Size Is Still Large

The repository only contains pointers, not data. If it's larger:

1. Check if data is accidentally committed (should never happen with filters configured):
   ```bash
   du -sh .git
   git count-objects -v
   ```

2. Data files live in the **cache**, not the repository:
   ```bash
   # Cache is outside the repo (per-user, per-machine)
   # Find it:
   git drs cache info
   ```

## Additional Resources

### Documentation & Specifications

- **git-drs Repository**: https://github.com/calypr/git-drs
- **git-drs Documentation**: https://github.com/calypr/git-drs/blob/main/README.md
- **ANVIL + Terra POC Design**: `docs/anvil-terra-poc.md` (in git-drs repo)
- **GA4GH DRS Specification**: https://github.com/ga4gh/data-repository-service-schemas

### ANVIL & Data Access

- **ANVIL Project Website**: https://www.anvilproject.org
- **ANVIL Data Explorer**: https://explore.anvilproject.org
- **ANVIL Documentation**: https://anvilproject.org/learn
- **Terra Platform**: https://app.terra.bio

### Related Projects

- **1000 Genomes Project**: https://www.internationalgenome.org
- **1000 Genomes PRIMED**: https://www.internationalgenome.org/1000-genomes-primed-project

## Contributing

This repository is a **reference proof-of-concept**. Changes to the reference model or workflow should:

1. **For data updates:** Contact the ANVIL PRIMED project stewards
2. **For git-drs improvements:** Submit issues and PRs to https://github.com/calypr/git-drs
3. **For documentation:** Edit README.md or related documentation in this repo

**Adding new files:**

```bash
# Get DRS URI from ANVIL Data Explorer
git drs add-ref --remote anvil drs://drs.anv0:v2_<object-id> <path>/<filename.tsv>

# Validate (dry-run)
git drs add-ref --remote anvil --manifest references.tsv --dry-run

# Commit and publish
git add .gitattributes
git commit -m "Add reference to <description>"
git push
```

## License & Data Use

This repository contains **pointers to** data from the ANVIL/1000 Genomes Project PRIMED initiative. The actual data use policy depends on the dataset's consent group and data use permissions:

- **Access terms** are enforced by ANVIL/Terra at authorization time
- **Pointers in Git** are subject to standard open-source licensing
- **Actual data bytes** are governed by the ANVIL Data Use Agreements

See https://www.anvilproject.org/data for details on specific datasets and their data use agreements.

## Support & POC Status

### Known Limitations

This is a **reference proof-of-concept**. Features still in development:

- **Producer setup:** Safe clone-local remote configuration mechanism
- **Resilience:** Expired-URL re-resolution and bounded retry
- **Performance:** Concurrent manifest validation and downloads
- **Compatibility:** Independent two-user, denied-user, and credential-leak testing

### Getting Help

- **ANVIL Support**: https://www.anvilproject.org/support
- **git-drs Issues**: https://github.com/calypr/git-drs/issues
- **Terra Support**: https://support.terra.bio
- **Documentation**: See `docs/anvil-terra-poc.md` in the git-drs repository

---

**Repository Type**: Reference proof-of-concept for git-drs + ANVIL integration  
**Last Updated**: August 2026  
**POC Status**: Vertical slice implemented; production validation in progress
