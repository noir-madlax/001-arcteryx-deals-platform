import base64
import gzip
import hashlib
import json
import unittest

from tools.prepare_price_audit_sample import (
    SamplePayloadError,
    decode_sample_payload,
)


def artifact_bytes():
    counts = {
        "arcteryx_outlet": 60,
        "evo": 10,
        "mec": 10,
        "rei": 10,
        "ssense": 10,
    }
    audits = [
        {"sku_id": f"{dealer}:{index}", "dealer": dealer}
        for dealer, count in counts.items()
        for index in range(count)
    ]
    return json.dumps({"sample_seed": 123, "audits": audits}).encode("utf-8")


class PriceAuditSampleTests(unittest.TestCase):
    def test_decodes_hash_bound_exact_sample(self):
        raw = artifact_bytes()
        payload = base64.b64encode(gzip.compress(raw)).decode("ascii")

        decoded = decode_sample_payload(payload, hashlib.sha256(raw).hexdigest())

        self.assertEqual(decoded, raw)

    def test_rejects_sha_mismatch(self):
        raw = artifact_bytes()
        payload = base64.b64encode(gzip.compress(raw)).decode("ascii")

        with self.assertRaisesRegex(SamplePayloadError, "sha256 mismatch"):
            decode_sample_payload(payload, "0" * 64)

    def test_rejects_wrong_dealer_contract(self):
        source = json.loads(artifact_bytes())
        source["audits"][0]["dealer"] = "evo"
        raw = json.dumps(source).encode("utf-8")
        payload = base64.b64encode(gzip.compress(raw)).decode("ascii")

        with self.assertRaisesRegex(SamplePayloadError, "dealer counts"):
            decode_sample_payload(payload, hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
