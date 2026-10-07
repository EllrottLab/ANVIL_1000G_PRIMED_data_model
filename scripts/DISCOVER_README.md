# Discover cohort authentication requirements

[`discover_auth.py`](discover_auth.py) reports the authentication advertised for
this cohort's DRS objects and explains what still requires provider setup.
It uses Python 3's standard library. It does not load credentials, start login,
exchange tokens, or download genomic payloads.

## Quick start

From the git-drs repository root:

```bash
python3 scripts/discover_auth.py \
  > /tmp/cohort-auth.json
```

Defaults resolve relative to the script, regardless of the working directory.
Network access is needed for live discovery. No Google login is needed to run
these anonymous probes.

## Inputs and scope

The default input is the single TSV manifest under the data directory's `etc/`.
The manifest must be readable TSV, with `files.drs_uri` and `datasets.title`
columns. Rows are filtered by exact dataset title, and DRS IDs are deduplicated.
Supported URIs have the form `drs://drs.anv0:OBJECT_ID`; this is a cohort-specific
utility, not a general DRS namespace resolver.

The supplied manifest contains seven **data-model file IDs**, not a complete
inventory of genomic payload IDs. If `sequencing_file.tsv` is hydrated, its
`file_path` column supplies counts of `gs://` references by bucket. These counts
cover the entire local table, not a selected sample set or unique subjects.
Missing or unhydrated sequencing metadata may produce empty counts.

| Option | Default | Purpose |
| --- | --- | --- |
| `--data-dir PATH` | Script's parent data directory | Locate `etc/` and optional `sequencing_file.tsv` |
| `--manifest PATH` | Single `etc/*.tsv` | Select a saved manifest explicitly; required if none or multiple exist |
| `--dataset TITLE` | `ANVIL_1000G_PRIMED_data_model` | Filter manifest rows by exact title |
| `--drs-base URL` | `https://data.terra.bio/ga4gh/drs/v1` | Explicit API base mapped to `drs.anv0`; include the API prefix |
| `--catalog-url URL` | None | Optionally probe a known HTTPS catalog query and its auth metadata |
| `--timeout SECONDS` | `15` | Positive timeout passed to each network request; not a total runtime limit |

Explicit relative paths are resolved from the current working directory.
For example, from the dataset directory:

```bash
python3 scripts/discover_auth.py --manifest /path/to/anvil-manifest.tsv \
  --timeout 10 > /tmp/cohort-auth.json
```

## Discovery steps

1. Read the saved manifest and select the cohort's IDs.
2. Send anonymous `OPTIONS` to `<drs-base>/objects`, with a JSON
   `bulk_object_ids` array.
3. Read per-object authorization from `resolved_drs_object`. Missing or duplicate
   bulk entries trigger individual `OPTIONS /objects/{id}` probes. This also
   handles unavailable bulk discovery. A failed bulk request prints its HTTP
   status or network failure to stderr before the individual probes run; the
   JSON report keeps the same information in `drs.bulk_probe`.
4. Preserve each object's supported types as **alternatives**, together with
   bearer and Passport visa issuer lists.
5. If `--catalog-url` is supplied, make an anonymous GET. Look for a quoted
   `resource_metadata` URL in `WWW-Authenticate`, otherwise try the RFC 9728
   well-known metadata location derived from that URL. Accept catalog metadata
   only when its `resource` exactly matches the supplied catalog URL.
6. Probe discovered bearer issuers and catalog authorization servers for OIDC
   metadata, then OAuth metadata if necessary. Require an exact `issuer` match.
   Report endpoints and flow capabilities; do not execute the advertised flows.
7. Add the existing Terra/Google ADC setup hint and local storage-reference
   counts, explicitly distinguished from live auth discovery.

Requests use HTTPS, refuse redirects, and limit JSON response parsing to 1 MiB.
Non-object or invalid JSON is not accepted as metadata. Discovery follows URLs
advertised by services; review the catalog, API base, and manifest you supply.
Endpoint metadata is evidence of capabilities, not a grant of permission.

## The catalog prerequisite

This script starts with a **saved manifest**, so it already has the IDs needed
for DRS `OPTIONS`. It cannot use object-level discovery to obtain that initial
list. Even with `--catalog-url`, a manifest remains required: the optional probe
is diagnostic and runs after the DRS probes. It does not search a catalog,
export IDs, or implement a catalog-only workflow.

When starting without IDs, first identify the catalog/workspace and obtain a
manifest through its API or UI. A catalog supporting RFC 9728 can advertise its
authorization servers before login. Otherwise its provider instructions or
configured helper must identify the authentication flow. A bare `401 Bearer`
challenge is insufficient. Pass the actual catalog API query URL to
`--catalog-url`, not a payload URL or a portal landing page.

## Reading the JSON report

| Field | Meaning |
| --- | --- |
| `dataset` | Selected manifest dataset title |
| `catalog` | Manifest source and optional catalog/metadata probe results |
| `drs.endpoint` | Explicit API mapping used for these IDs |
| `drs.bulk_probe` | Bulk HTTP status and any diagnostic information |
| `drs.objects` | Per-ID auth alternatives, issuer lists, or unresolved gaps |
| `issuer_discovery` | Validated issuer metadata or failed discovery attempts |
| `provider_hint` | Repository-defined Google ADC setup advice, not a discovered requirement |
| `payload` | Local bucket-reference counts and the unverified storage-access gap |

An abbreviated example of an individual object's result:

```json
{
  "alternatives": ["PassportAuth", "BearerAuth"],
  "bearer_auth_issuers": [],
  "passport_auth_issuers": ["https://sts.nih.gov"],
  "bearer_gap": "No bearer issuer advertised; use configured provider knowledge",
  "passport_gap": "Visa issuers do not identify a login provider; configure a Passport broker"
}
```

During the initial live check, bulk discovery returned 404 and individual
probes returned the alternatives above for all seven IDs. Terra returned a
null bearer-issuer field, which the script normalizes to an empty list. This
observation is not a permanent provider contract; rerun discovery for current
results.

## Remaining authentication gaps

- A missing bearer issuer requires configured provider knowledge. The reported
  `gcloud auth application-default login` command comes from this repository's
  Terra setup, not the live object response.
- A Passport visa issuer identifies who issued a visa, not necessarily a login
  endpoint or Passport broker. The script does not probe visa issuers as OIDC
  providers; obtaining a Passport requires a broker/provider integration.
- OAuth/OIDC metadata can advertise endpoints and supported grants, but usable
  client registration, exact scopes, audience, and permission to use a flow
  still need configuration. The script does not dynamically register clients.
- Catalog visibility, DRS metadata permission, access-URL authorization, and
  payload-storage permission are separate. The script does not retrieve
  `DrsObject` metadata/access methods or verify GCS access, account linking,
  RAS consent, or data-access entitlements. Manifest consent labels are not
  interpreted as login requirements.

## Errors and exit status

- Exit **0** means a report was produced, including reports with unresolved
  gaps. It does not mean that login or download permission was verified.
- Exit **1** reports caught input/file errors on stderr. Examples include no
  unique manifest, missing columns, no matching dataset, and unsupported URIs.
- Exit **2** indicates CLI argument errors, including a nonpositive timeout.
- Connection/TLS failures during request opening appear as `status: null` with
  requirements unknown. Some response-reading failures can terminate the run.
- HTTP 204/405 on individual discovery records the specification's `None`
  default but explicitly leaves requirements unknown. It is not proof of public
  access. Other HTTP failures, redirects, and unusable responses also leave gaps.
- No automatic login or credential retry is performed after a 401/403.

## Offline checks and code navigation

From the dataset directory:

```bash
python3 -m unittest discover -s scripts -p 'test_discover_auth.py' -v
```

Checks cover partial bulk fallback, authentication alternatives, unsupported
versus public discovery, Terra's null issuer field, exact issuer matching, and
OIDC/OAuth well-known URL construction. They use fake probes and no network.

The script's functions follow the flow directly: `main` parses options,
`discover` assembles the report, `discover_objects` probes DRS,
`authorization` normalizes auth fields, and `issuer_metadata` probes providers.
`request`, `https_url`, and `NoRedirect` implement the anonymous HTTP boundary.

## References

- [ADR: issue 260](https://github.com/calypr/git-drs/issues/260)
- [DRS bulk objects schema](https://github.com/ga4gh/data-repository-service-schemas/blob/master/openapi/paths/bulkobjects%40%7Bobject_id%7D.yaml)
- [DRS Authorizations schema](https://github.com/ga4gh/data-repository-service-schemas/blob/master/openapi/components/schemas/Authorizations.yaml)
- [OpenID Connect Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html)
- [RFC 8414: OAuth Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414.html)
- [RFC 9728: OAuth Protected Resource Metadata](https://www.rfc-editor.org/rfc/rfc9728.html)


## Discovered auth information

```json

{
  "dataset": "ANVIL_1000G_PRIMED_data_model",
  "catalog": {
    "ids_source": "etc/anvil-manifest-38dc7537-aee9-53c1-a7c2-9c817b17ac5c.3b87509e-87fe-5024-a086-44cb81aa7de7.tsv",
    "gap": "Saved IDs bypass catalog login; export/query authentication is separate"
  },
  "drs": {
    "endpoint": "https://data.terra.bio/ga4gh/drs/v1",
    "bulk_probe": {
      "status": 404
    },
    "objects": {
      "v2_093066ee-45f8-3664-9363-c602913ef0c7": {
        "alternatives": [
          "PassportAuth",
          "BearerAuth"
        ],
        "bearer_auth_issuers": [],
        "passport_auth_issuers": [
          "https://sts.nih.gov"
        ],
        "bearer_gap": "No bearer issuer advertised; use configured provider knowledge",
        "passport_gap": "Visa issuers do not identify a login provider; configure a Passport broker"
      },
      "v2_6d1cf5f0-99a8-3cd9-b580-01102f3abfe7": {
        "alternatives": [
          "PassportAuth",
          "BearerAuth"
        ],
        "bearer_auth_issuers": [],
        "passport_auth_issuers": [
          "https://sts.nih.gov"
        ],
        "bearer_gap": "No bearer issuer advertised; use configured provider knowledge",
        "passport_gap": "Visa issuers do not identify a login provider; configure a Passport broker"
      },
      "v2_a31c73cb-3bc8-3688-a1e5-05f2d63d0cf9": {
        "alternatives": [
          "PassportAuth",
          "BearerAuth"
        ],
        "bearer_auth_issuers": [],
        "passport_auth_issuers": [
          "https://sts.nih.gov"
        ],
        "bearer_gap": "No bearer issuer advertised; use configured provider knowledge",
        "passport_gap": "Visa issuers do not identify a login provider; configure a Passport broker"
      },
      "v2_b6b829f3-6046-3f29-896f-495a23f24c14": {
        "alternatives": [
          "PassportAuth",
          "BearerAuth"
        ],
        "bearer_auth_issuers": [],
        "passport_auth_issuers": [
          "https://sts.nih.gov"
        ],
        "bearer_gap": "No bearer issuer advertised; use configured provider knowledge",
        "passport_gap": "Visa issuers do not identify a login provider; configure a Passport broker"
      },
      "v2_d6f6836d-688a-33b9-b3d9-f4e829830c0e": {
        "alternatives": [
          "PassportAuth",
          "BearerAuth"
        ],
        "bearer_auth_issuers": [],
        "passport_auth_issuers": [
          "https://sts.nih.gov"
        ],
        "bearer_gap": "No bearer issuer advertised; use configured provider knowledge",
        "passport_gap": "Visa issuers do not identify a login provider; configure a Passport broker"
      },
      "v2_d8add534-63b4-3077-9df5-5ebc8d138415": {
        "alternatives": [
          "PassportAuth",
          "BearerAuth"
        ],
        "bearer_auth_issuers": [],
        "passport_auth_issuers": [
          "https://sts.nih.gov"
        ],
        "bearer_gap": "No bearer issuer advertised; use configured provider knowledge",
        "passport_gap": "Visa issuers do not identify a login provider; configure a Passport broker"
      },
      "v2_e68887be-c583-375a-a773-48771192c8fa": {
        "alternatives": [
          "PassportAuth",
          "BearerAuth"
        ],
        "bearer_auth_issuers": [],
        "passport_auth_issuers": [
          "https://sts.nih.gov"
        ],
        "bearer_gap": "No bearer issuer advertised; use configured provider knowledge",
        "passport_gap": "Visa issuers do not identify a login provider; configure a Passport broker"
      }
    }
  },
  "issuer_discovery": {},
  "provider_hint": {
    "source": "Cohort README and git-drs Terra preset, not live discovery",
    "auth": "google-adc",
    "setup": "gcloud auth application-default login",
    "gap": "Login does not establish dataset permission or supply a Passport"
  },
  "payload": {
    "gs_bucket_file_counts": {
      "fc-2ee2ca2a-a140-48a1-b793-e27badb7945d": 8611,
      "terra-featured-workspaces": 23
    },
    "gap": "Storage access and access-method authorization unverified; metadata auth does not prove byte access. Empty counts may mean unhydrated tables."
  }
}

```