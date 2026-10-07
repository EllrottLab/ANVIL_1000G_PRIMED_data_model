#!/usr/bin/env python3
"""Report cohort auth discovery without loading credentials or downloading payloads."""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

DATA = Path(__file__).resolve().parents[1]
TERRA = "https://data.terra.bio/ga4gh/drs/v1"


class NoRedirect(HTTPRedirectHandler):
    """Keep anonymous probes on the requested endpoint by refusing redirects."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Return no replacement request so urllib exposes the redirect status."""
        return None


def https_url(value):
    """Return an HTTPS URL, or raise ValueError for missing host, userinfo or fragment."""
    u = urlsplit(value)
    if u.scheme != "https" or not u.hostname or u.username or u.password or u.fragment:
        raise ValueError("Expected an HTTPS URL without userinfo or fragment")
    return value


def request(url, method="GET", body=None, timeout=15):
    """Return (HTTP summary, JSON object) from an anonymous HTTPS probe.

    Encode body as JSON when supplied. Refuse redirects and accept at most 1 MiB
    of JSON object content. HTTP errors retain their status; connection failures
    return status None. Invalid/non-object bodies become an empty dictionary.
    """
    https_url(url)
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        response = build_opener(NoRedirect()).open(req, timeout=timeout)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError, OSError):
        return {"status": None, "error": "Network or TLS failure; requirements unknown"}, {}
    with response:
        result = {"status": response.code}
        challenge = response.headers.get("WWW-Authenticate", "")
        if challenge:
            result["challenge_scheme"] = challenge.split()[0]
            match = re.search(r'\bresource_metadata="([^"]+)"', challenge)
            if match:
                result["resource_metadata"] = match[1]
        raw = response.read(1024 * 1024 + 1)
        try:
            value = json.loads(raw) if len(raw) <= 1024 * 1024 else None
        except (ValueError, UnicodeError):
            value = None
        if not isinstance(value, dict):
            result["body_note"] = "No bounded JSON object returned"
            value = {}
        return result, value


def issuer_metadata(issuer, probe):
    """Discover OIDC then OAuth metadata whose issuer exactly matches the input.

    probe accepts a URL and returns (HTTP summary, JSON object). Return selected
    metadata fields or failed attempts with a configuration gap; never log in.
    Invalid issuer URLs raise ValueError.
    """
    https_url(issuer)
    u = urlsplit(issuer)
    if u.query:
        raise ValueError("Issuer must not contain a query")
    urls = [issuer.rstrip("/") + "/.well-known/openid-configuration",
            f"https://{u.netloc}/.well-known/oauth-authorization-server{u.path.rstrip('/')}" ]
    attempts = []
    for url in urls:
        result, data = probe(url)
        attempts.append(result)
        if result["status"] == 200 and data.get("issuer") == issuer:
            fields = ("issuer", "authorization_endpoint", "token_endpoint",
                      "device_authorization_endpoint", "grant_types_supported",
                      "code_challenge_methods_supported", "scopes_supported",
                      "registration_endpoint", "token_endpoint_auth_methods_supported")
            return {"metadata": {k: data[k] for k in fields if k in data},
                    "gap": "Client registration, permitted flow, exact scopes and audience still required"}
    return {"attempts": attempts, "gap": "No matching issuer metadata; configure provider helper"}


def authorization(data):
    """Normalize one DRS authorization object into alternatives and issuer lists.

    Missing/empty types default to None; missing/null issuer lists become empty.
    Invalid types or issuer lists produce a gap instead of usable requirements.
    """
    types = data.get("supported_types") or ["None"]
    if not isinstance(types, list) or any(t not in ("None", "BasicAuth", "BearerAuth", "PassportAuth") for t in types):
        return {"gap": "Invalid supported_types"}
    result = {"alternatives": types}
    for key in ("bearer_auth_issuers", "passport_auth_issuers"):
        issuers = data.get(key)
        if issuers is None:
            issuers = []
        if not isinstance(issuers, list) or any(not isinstance(i, str) for i in issuers):
            return {"gap": "Invalid issuer list"}
        result[key] = issuers
    if "BearerAuth" in types and not result["bearer_auth_issuers"]:
        result["bearer_gap"] = "No bearer issuer advertised; use configured provider knowledge"
    if "PassportAuth" in types:
        result["passport_gap"] = "Visa issuers do not identify a login provider; configure a Passport broker"
    return result


def discover_objects(base, ids, probe):
    """Return per-ID auth requirements using bulk OPTIONS with individual fallback.

    base includes the DRS API prefix. probe accepts URL, method and optional JSON
    body and returns (HTTP summary, JSON object). Missing or duplicate bulk rows
    trigger individual probes; unsupported discovery remains explicitly unknown.
    """
    base = https_url(base).rstrip("/")
    bulk, data = probe(base + "/objects", "OPTIONS", {"bulk_object_ids": ids})
    if bulk["status"] != 200:
        detail = bulk.get("error") or bulk.get("body_note") or "bulk discovery unavailable"
        print(f"bulk DRS OPTIONS {base}/objects failed (HTTP {bulk['status']}): {detail}; trying per-object OPTIONS", file=sys.stderr)
    rows = data.get("resolved_drs_object", []) if bulk["status"] == 200 else []
    by_id = {}
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("drs_object_id"), str):
                by_id.setdefault(row["drs_object_id"], []).append(row)
    objects = {}
    for oid in ids:
        matches = by_id.get(oid, [])
        if len(matches) == 1:
            objects[oid] = authorization(matches[0])
            continue
        result, row = probe(base + "/objects/" + quote(oid, safe=""), "OPTIONS")
        if result["status"] == 200 and row and row.get("drs_object_id", oid) == oid:
            objects[oid] = authorization(row)
        else:
            objects[oid] = {**result, "gap": "Requirements unknown; configure provider or consult its documentation"}
            if result["status"] in (204, 405):
                objects[oid]["spec_default"] = "None; discovery unsupported, not proof of public access"
    return {"endpoint": base, "bulk_probe": bulk, "objects": objects}


def discover(args):
    """Build the cohort report from CLI options, saved IDs and anonymous probes.

    Require an AnVIL manifest even when probing an optional catalog. Inspect
    local sequencing-file paths for bucket counts without fetching those files.
    Return a JSON-serializable report; invalid input raises ValueError or OSError.
    """
    manifests = sorted((args.data_dir / "etc").glob("*.tsv"))
    manifest = args.manifest or (manifests[0] if len(manifests) == 1 else None)
    if manifest is None:
        raise ValueError("Provide --manifest: no unique saved manifest in etc/")
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"files.drs_uri", "datasets.title"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError("Manifest must contain files.drs_uri and datasets.title; hydrate it first")
        rows = list(reader)
    rows = [r for r in rows if r.get("datasets.title") == args.dataset]
    if not rows:
        raise ValueError("Dataset not found in manifest")
    ids = set()
    for row in rows:
        uri = row.get("files.drs_uri") or ""
        if not re.fullmatch(r"drs://drs\.anv0:[A-Za-z0-9_.-]+", uri):
            raise ValueError("Expected AnVIL compact DRS identifiers in this cohort manifest")
        ids.add(uri.split(":", 2)[2])
    def probe(url, method="GET", body=None):
        """Apply the CLI timeout to each anonymous discovery request."""
        return request(url, method, body, args.timeout)
    drs = discover_objects(args.drs_base, sorted(ids), probe)
    catalog_url = args.catalog_url
    catalog = {"ids_source": str(manifest), "gap": "Saved IDs bypass catalog login; export/query authentication is separate"}
    if catalog_url:
        result, _ = probe(catalog_url)
        catalog["probe"] = result
        u = urlsplit(catalog_url)
        metadata_url = result.get("resource_metadata", f"https://{u.netloc}/.well-known/oauth-protected-resource{u.path.rstrip('/')}")
        status, metadata = probe(metadata_url)
        catalog["metadata_probe"] = status
        if status["status"] == 200 and metadata.get("resource") == catalog_url:
            catalog["authorization_servers"] = metadata.get("authorization_servers", [])
            catalog["scopes_supported"] = metadata.get("scopes_supported", [])
        else:
            catalog["gap"] = "No matching RFC 9728 metadata; use catalog provider instructions. A Bearer challenge alone is insufficient."
    issuers = {i for obj in drs["objects"].values() for i in obj.get("bearer_auth_issuers", [])}
    servers = catalog.get("authorization_servers", [])
    if isinstance(servers, list):
        issuers.update(i for i in servers if isinstance(i, str))
    discovered = {}
    for issuer in sorted(issuers):
        try:
            discovered[issuer] = issuer_metadata(issuer, probe)
        except ValueError:
            discovered[issuer] = {"gap": "Invalid issuer URL"}
    buckets = Counter()
    table = args.data_dir / "sequencing_file.tsv"
    if table.exists():
        with table.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                url = urlsplit(row.get("file_path", ""))
                if url.scheme == "gs":
                    buckets[url.netloc] += 1
    return {"dataset": args.dataset, "catalog": catalog, "drs": drs,
            "issuer_discovery": discovered,
            "provider_hint": {"source": "Cohort README and git-drs Terra preset, not live discovery",
                              "auth": "google-adc", "setup": "gcloud auth application-default login",
                              "gap": "Login does not establish dataset permission or supply a Passport"},
            "payload": {"gs_bucket_file_counts": dict(buckets),
                        "gap": "Storage access and access-method authorization unverified; metadata auth does not prove byte access. Empty counts may mean unhydrated tables."}}


def main():
    """Parse CLI options and print JSON, reporting input failures on stderr."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--dataset", default="ANVIL_1000G_PRIMED_data_model")
    parser.add_argument("--drs-base", default=TERRA, help="Explicit API base for drs.anv0; includes /ga4gh/drs/v1")
    parser.add_argument("--catalog-url", help="Optional actual catalog query URL; never a payload URL")
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        print(json.dumps(discover(args), indent=2))
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
