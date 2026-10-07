"""Offline checks for partial DRS discovery and issuer validation."""
import io
import unittest
from contextlib import redirect_stderr
from discover_auth import authorization, discover_objects, issuer_metadata


class DiscoveryTest(unittest.TestCase):
    """Check fallback and validation behavior without making network requests."""
    def test_bulk_failure_is_logged_to_stderr(self):
        """Report the failed bulk attempt and still try individual discovery."""
        calls = []

        def probe(url, method="GET", body=None):
            """Simulate an unavailable bulk endpoint and one working object endpoint."""
            calls.append((url, method, body))
            if body is not None:
                return {"status": 404}, {}
            return {"status": 200}, {"supported_types": ["BearerAuth"]}

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = discover_objects("https://drs.example/ga4gh/drs/v1", ["a"], probe)
        self.assertIn("bulk DRS OPTIONS", stderr.getvalue())
        self.assertIn("HTTP 404", stderr.getvalue())
        self.assertEqual(result["objects"]["a"]["alternatives"], ["BearerAuth"])
        self.assertEqual([call[1] for call in calls], ["OPTIONS", "OPTIONS"])

    def test_partial_bulk_fallback_and_unknown_are_distinct_from_public(self):
        """Preserve alternatives and gaps across partial bulk and null-issuer replies."""
        calls = []

        def probe(url, method="GET", body=None):
            """Record requests and simulate partial bulk success plus unsupported fallback."""
            calls.append((url, method, body))
            if body:
                return {"status": 200}, {"resolved_drs_object": [
                    {"drs_object_id": "a", "supported_types": ["BearerAuth", "PassportAuth"],
                     "bearer_auth_issuers": ["https://issuer.example"],
                     "passport_auth_issuers": ["https://visa.example"]}]}
            return {"status": 204}, {}

        result = discover_objects("https://drs.example/ga4gh/drs/v1", ["a", "b"], probe)
        self.assertEqual(result["objects"]["a"]["alternatives"], ["BearerAuth", "PassportAuth"])
        self.assertIn("passport_gap", result["objects"]["a"])
        self.assertIn("gap", result["objects"]["b"])
        self.assertNotIn("alternatives", result["objects"]["b"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][2], {"bulk_object_ids": ["a", "b"]})
        self.assertEqual(authorization({})["alternatives"], ["None"])
        self.assertIn("gap", authorization({"supported_types": "BearerAuth"}))
        terra = authorization({"supported_types": ["BearerAuth", "PassportAuth"],
                               "bearer_auth_issuers": None,
                               "passport_auth_issuers": ["https://sts.nih.gov"]})
        self.assertEqual(terra["bearer_auth_issuers"], [])
        self.assertIn("bearer_gap", terra)

    def test_issuer_must_match_and_oauth_path_differs(self):
        """Reject mismatched issuers and check the two well-known URL layouts."""
        urls = []

        def probe(url):
            """Record discovery URLs and return metadata for the wrong issuer."""
            urls.append(url)
            return {"status": 200}, {"issuer": "https://wrong.example"}

        result = issuer_metadata("https://issuer.example/tenant", probe)
        self.assertIn("gap", result)
        self.assertNotIn("metadata", result)
        self.assertEqual(urls, [
            "https://issuer.example/tenant/.well-known/openid-configuration",
            "https://issuer.example/.well-known/oauth-authorization-server/tenant"])
        with self.assertRaises(ValueError):
            issuer_metadata("http://issuer.example", probe)


if __name__ == "__main__":
    unittest.main()
