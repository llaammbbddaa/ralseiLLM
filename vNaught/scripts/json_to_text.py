#!/usr/bin/env python3
"""
json_to_text.py

Recursively extract all string and numeric values from a JSON file and
write them as plain text (one item per line) to an output file.

Usage:
    python scripts/json_to_text.py input.json output.txt

This keeps only the textual contents and removes JSON punctuation/structure.
"""
import sys
import json
from typing import Any, Set


def extract_texts(obj: Any, texts: Set[str]):
    """Recursively walk JSON and collect string/number values as strings."""
    if obj is None:
        return
    if isinstance(obj, (str,)):
        s = obj.strip()
        if s:
            texts.add(s)
        return
    if isinstance(obj, (int, float)):
        texts.add(str(obj))
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            # also include keys (optional) -- include them to not lose headings
            if isinstance(k, str) and k.strip():
                texts.add(k.strip())
            extract_texts(v, texts)
        return
    if isinstance(obj, (list, tuple, set)):
        for item in obj:
            extract_texts(item, texts)
        return


def main():
    if len(sys.argv) < 3:
        print("Usage: json_to_text.py input.json output.txt")
        sys.exit(2)

    in_path = sys.argv[1]
    out_path = sys.argv[2]

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = set()
    extract_texts(data, texts)

    # write sorted to produce stable output
    with open(out_path, "w", encoding="utf-8") as f:
        for line in sorted(texts):
            f.write(line + "\n")


if __name__ == "__main__":
    main()
