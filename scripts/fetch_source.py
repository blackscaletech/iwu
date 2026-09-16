"""Retrieve one pinned public data file; never executes upstream code."""
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
REV = "52cb829c7a2efb2d659285c4b1768d191d97f8d2"
URL = f"https://raw.githubusercontent.com/METR/eval-analysis-public/{REV}/reports/time-horizon-1-0/data/raw/runs.jsonl"

def main():
    dest = ROOT / "sources" / "metr_runs.jsonl"
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = urllib.request.urlopen(URL, timeout=90).read()
    digest = hashlib.sha256(data).hexdigest()
    expected="f489d11728909937dad99ba1ed2d7c40efe12a766891e67dbc7c2486a3311236"
    if digest != expected:
        raise ValueError("Pinned source digest mismatch; received bytes were discarded")
    meta = {
        "source": "METR/eval-analysis-public", "revision": REV,
        "url": URL, "sha256": digest, "bytes": len(data),
        "local_filename": "sources/metr_runs.jsonl",
        "source_license_note": "No license file identified in the pinned tree. Fetch directly from upstream for research reanalysis; raw data and upstream code are excluded from the distributable bundle.",
        "retrieval_date": "2026-09-15"
    }
    dest.write_bytes(data)
    (ROOT / "sources" / "PROVENANCE.json").write_text(json.dumps(meta, indent=2) + "\n")
    first = json.loads(data.splitlines()[0])
    print(json.dumps({"provenance": meta, "first_record_keys": list(first),
                      "first_record_field_types": {k:type(v).__name__ for k,v in first.items()}}, indent=2))

if __name__ == "__main__":
    main()
