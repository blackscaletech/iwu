"""Check the small publication boundary for consistency and stale material."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".cff", ".json", ".md", ".mjs", ".py", ".toml", ".txt", ""}


def main() -> None:
    files = sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and ".git" not in path.parts
        and path.suffix in TEXT_SUFFIXES
    )
    disallowed_identity = "".join(
        chr(code) for code in (104, 101, 108, 108, 111, 114, 101, 105, 108, 97)
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        if disallowed_identity in text.lower():
            raise SystemExit(f"disallowed attribution in {path.relative_to(ROOT)}")
        if path.suffix == ".json":
            json.loads(text)

    lock = json.loads((ROOT / "validation" / "PROTOCOL-LOCK.json").read_text())
    protocol = ROOT / "validation" / lock["file"]
    digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    if digest != lock["sha256"]:
        raise SystemExit("validation protocol commitment mismatch")

    link_pattern = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
    for path in (ROOT / "README.md", ROOT / "SPECIFICATION.md", ROOT / "VALIDATION.md"):
        for target in link_pattern.findall(path.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            clean = target.split("#", 1)[0]
            if clean and not (path.parent / clean).exists():
                raise SystemExit(f"broken internal link {target!r} in {path.name}")

    package = json.loads((ROOT / "package.json").read_text())
    if package.get("author") != "blackscaletech":
        raise SystemExit("unexpected JavaScript author")
    pyproject = (ROOT / "pyproject.toml").read_text()
    citation = (ROOT / "CITATION.cff").read_text()
    if 'authors = [{name = "blackscaletech"}]' not in pyproject:
        raise SystemExit("unexpected Python author")
    if "  - name: blackscaletech" not in citation:
        raise SystemExit("unexpected citation author")

    print(f"repository audit passed: {len(files)} text files")


if __name__ == "__main__":
    main()
