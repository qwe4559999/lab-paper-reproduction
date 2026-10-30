#!/usr/bin/env python3
"""Read-only inventory for paper-figure reproduction.

Usage:
    python inventory_inputs.py <input_dir> --out inventory.json
    python inventory_inputs.py <input_dir> --out inventory.json --no-hash

It never writes inside the input directory. Unknown extensions are listed, not
silently ignored. Large files can skip hashing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

TEXT_EXT = {".csv", ".tsv", ".txt", ".dat", ".prn", ".asc"}
TABLE_EXT = {".xlsx", ".xlsm", ".xls", ".ods"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".emf", ".wmf", ".svg", ".pdf"}
SPECTRUM_EXT = {".spa", ".sp", ".jdx", ".dx", ".irs"}
FIT_WORDS = re.compile(r"(fit|peak|分峰|拟合|component|deconv)", re.I)
PROCESS_WORDS = re.compile(r"(smooth|baseline|normaliz|归一|平滑|基线)", re.I)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def decode_head(path: Path, n: int = 8) -> list[str]:
    raw = path.read_bytes()[:16384]
    for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return []
    return [ln.rstrip("\r\n") for ln in text.splitlines()[:n] if ln.strip()]


def text_header(path: Path) -> list[str] | None:
    lines = decode_head(path)
    if not lines:
        return None
    first = max(lines[:5], key=lambda s: sum(s.count(c) for c in "\t,;"))
    for delim in ("\t", ",", ";"):
        if delim in first:
            return [p.strip() for p in first.split(delim)][:20]
    return [first[:200]]


def xlsx_header(path: Path) -> dict | None:
    try:
        from openpyxl import load_workbook
    except Exception:
        return None
    try:
        wb = load_workbook(path, read_only=True, data_only=True)
        out = {}
        for ws in wb.worksheets[:3]:
            for row in ws.iter_rows(min_row=1, max_row=8, values_only=True):
                vals = [str(v).strip() for v in row if v is not None and str(v).strip()]
                if vals:
                    out[ws.title] = vals[:20]
                    break
        wb.close()
        return out or None
    except Exception:
        return None


def classify(path: Path) -> str:
    ext = path.suffix.lower()
    name = path.stem
    if ext in IMAGE_EXT:
        return "figure"
    if ext in SPECTRUM_EXT:
        return "spectrum"
    if ext in TABLE_EXT or ext in TEXT_EXT:
        if FIT_WORDS.search(name):
            return "fit_export"
        if PROCESS_WORDS.search(name):
            return "processed"
        return "table_or_export"
    if FIT_WORDS.search(name):
        return "fit_export"
    if PROCESS_WORDS.search(name):
        return "processed"
    return "unknown"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir")
    ap.add_argument("--out", default="inventory.json")
    ap.add_argument("--no-hash", action="store_true")
    ap.add_argument("--max-hash-mb", type=float, default=200.0)
    args = ap.parse_args()

    root = Path(args.input_dir).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")
    out = Path(args.out).resolve()
    if root == out.parent or root in out.parents:
        raise SystemExit("Refusing to write the inventory inside the input directory")

    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        ext = p.suffix.lower()
        item = {
            "path": str(p.relative_to(root)),
            "suffix": ext or "(none)",
            "bytes": p.stat().st_size,
            "kind": classify(p),
        }
        if not args.no_hash and item["bytes"] <= args.max_hash_mb * 1024 * 1024:
            item["sha256"] = sha256(p)
        elif not args.no_hash:
            item["sha256"] = None
            item["hash_skipped"] = f">{args.max_hash_mb:g} MB"
        if ext in TEXT_EXT:
            item["header"] = text_header(p)
        elif ext in TABLE_EXT:
            item["sheets"] = xlsx_header(p)
        files.append(item)

    by_kind = Counter(f["kind"] for f in files)
    by_ext = Counter(f["suffix"] for f in files)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_dir": str(root),
        "summary": {
            "files": len(files),
            "bytes": sum(f["bytes"] for f in files),
            "by_kind": dict(by_kind.most_common()),
            "by_suffix": dict(by_ext.most_common(30)),
        },
        "files": files,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print(f"\nwritten: {out}")
    print("\nfirst tables / exports:")
    for f in [x for x in files if x["kind"] in ("table_or_export", "fit_export")][:12]:
        hdr = f.get("header") or f.get("sheets")
        print(f"- {f['path']}  {hdr}")


if __name__ == "__main__":
    main()
