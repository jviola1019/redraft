"""Measure how often adding college distinguishes an eligible prospect within a class."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median


def evaluate(prospects, fields):
    keys = [tuple(row.get(field) for field in fields) for row in prospects]
    counts = Counter(keys)
    sizes = [counts[key] for key in keys]
    return {
        "uniqueProspects": sum(size == 1 for size in sizes),
        "fewerThanFive": sum(size < 5 for size in sizes),
        "medianMatchingProspects": median(sizes),
    }


def analyze(root):
    result = []
    for path in sorted((root / "data/processed").glob("scenario-[0-9]*.json")):
        data = path.read_bytes()
        rows = [p for p in json.loads(data)["prospects"] if p["playable"]]
        result.append({
            "year": int(path.stem.split("-")[1]),
            "sourceSha256": hashlib.sha256(data).hexdigest(),
            "prospects": len(rows),
            "missingCollege": sum(not p.get("college") for p in rows),
            "positionOnly": evaluate(rows, ["position"]),
            "collegePosition": evaluate(rows, ["college", "position"]),
            "positionHeightWeight": evaluate(rows, ["position", "heightIn", "weightLb"]),
        })
    if not result:
        raise ValueError("No versioned scenario files found")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    print(json.dumps(analyze(parser.parse_args().root), indent=2))
