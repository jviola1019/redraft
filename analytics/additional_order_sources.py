"""Normalize captured NFL draft-order source text; no runtime dependencies.

The ignored data/raw files are verbatim text returned by the web extractor, not
HTTP bytes. This tool emits provenance and owner sequences only.
"""
from __future__ import annotations

import hashlib
import json
import re
import csv
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "clean" / "additional_order_sources.json"
META = {
    2020: {
        "url": "https://static.clubs.nfl.com/image/upload/titans/ff4ybykwg15lmlhb9mne.pdf",
        "published": "2020-04-16", "modified": None, "round1": "2020-04-23T19:00:00-05:00",
        "asOf": "2020-04-15", "cutoffEvidence": "PDF title, order table, and footer say as of April 15, 2020; press release says FOR IMMEDIATE RELEASE — APRIL 16, 2020.",
        "usable": True,
    },
    2021: {
        "url": "https://amp.nfl.com/news/2021-nfl-draft-order-for-all-seven-rounds",
        "published": "2021-03-19T19:57:00", "modified": None, "round1": "2021-04-29T20:00:00-04:00",
        "asOf": None, "cutoffEvidence": "Published date precedes Round 1, but no modified timestamp or explicit order-as-of statement is exposed. Current body assigns No. 3 to San Francisco; the official 49ers page dates the Miami-to-San-Francisco trade to March 26, after the NFL.com March 19 publication date, proving the captured body is newer than its published timestamp.",
        "cutoffEvidenceUrl": "https://www.49ers.com/news/49ers-announce-trade-draft-dolphins",
        "usable": False,
    },
    2022: {
        "url": "https://amp.nfl.com/news/2022-nfl-draft-order-for-all-seven-rounds",
        "published": "2022-03-16T12:22:00", "modified": None, "round1": "2022-04-28T20:00:00-04:00",
        "asOf": "entering Day 1", "cutoffEvidence": "Editor's note: information below reflects the order entering Day 1 of the draft.",
        "usable": True,
    },
    2023: {
        "url": "https://www.nfl.com/news/2023-nfl-draft-order-for-all-seven-rounds",
        "published": None, "modified": None, "round1": "2023-04-27T20:00:00-04:00",
        "asOf": "beginning of Round 1", "cutoffEvidence": "Page states picks are accurate as of the beginning of Round 1; Published and Updated fields are blank in the captured page.",
        "usable": True,
    },
    2024: {
        "url": "https://amp.nfl.com/news/2024-nfl-draft-order-for-all-seven-rounds",
        "published": "2024-03-08T20:16:00", "modified": "2024-04-25T20:13:00", "round1": "2024-04-25T20:00:00-04:00",
        "asOf": "beginning of Round 1", "cutoffEvidence": "Page states picks are accurate as of the beginning of Round 1; page Updated timestamp is 13 minutes after Round 1 start.",
        "usable": True,
    },
}
ALIASES = {
    "arizona": "ARI", "arizona cardinals": "ARI", "atlanta": "ATL", "atlanta falcons": "ATL",
    "baltimore": "BAL", "baltimore ravens": "BAL", "buffalo": "BUF", "buffalo bills": "BUF",
    "carolina": "CAR", "carolina panthers": "CAR", "chicago": "CHI", "chicago bears": "CHI",
    "cincinnati": "CIN", "cincinnati bengals": "CIN", "cleveland": "CLE", "cleveland browns": "CLE",
    "dallas": "DAL", "dallas cowboys": "DAL", "denver": "DEN", "denver broncos": "DEN",
    "detroit": "DET", "detroit lions": "DET", "green bay": "GB", "green bay packers": "GB",
    "houston": "HOU", "houston texans": "HOU", "indianapolis": "IND", "indianapolis colts": "IND",
    "jacksonville": "JAX", "jacksonville jaguars": "JAX", "kansas city": "KC", "kansas city chiefs": "KC",
    "los angeles chargers": "LAC", "la chargers": "LAC", "l.a. chargers": "LAC",
    "los angeles rams": "LAR", "la rams": "LAR", "l.a. rams": "LAR",
    "las vegas": "LV", "las vegas raiders": "LV", "miami": "MIA", "miami dolphins": "MIA",
    "minnesota": "MIN", "minnesota vikings": "MIN", "new england": "NE", "new england patriots": "NE",
    "new orleans": "NO", "new orleans saints": "NO", "new york giants": "NYG", "ny giants": "NYG", "n.y. giants": "NYG",
    "new york jets": "NYJ", "ny jets": "NYJ", "n.y. jets": "NYJ", "philadelphia": "PHI", "philadelphia eagles": "PHI",
    "pittsburgh": "PIT", "pittsburgh steelers": "PIT", "san francisco": "SF", "san francisco 49ers": "SF",
    "seattle": "SEA", "seattle seahawks": "SEA", "tampa bay": "TB", "tampa bay buccaneers": "TB",
    "tennessee": "TEN", "tennessee titans": "TEN", "washington": "WAS", "washington redskins": "WAS",
    "washington football team": "WAS", "washington commanders": "WAS",
}
EXPECTED = {2020: 255, 2021: 259, 2022: 262, 2023: 259, 2024: 257}


def canonical(team: str) -> str:
    s = team.strip().lower().replace("\u00a0", " ")
    if s not in ALIASES:
        raise ValueError(f"Unmapped team label {team!r}")
    return ALIASES[s]


def parse(year: int, text: str) -> list[dict]:
    rows = []
    if year == 2020:
        start = text.find("Complete NFL Draft Order (as of April 15, 2020)")
        end = text.find("DRAFT PROSPECTS", start)
        body = text[start:end if end > start else None]
        rx = re.compile(r"^L\d+:\s*\| ([1-7])-(\d+)-(\d+) \| (.*?) \|$", re.M)
        for rnd, pick, overall, label in rx.findall(body):
            label = label.strip()
            comp = "*" in label or "compensatory" in label.lower()
            label = label.replace("*", "").strip()
            owner = re.split(r"\s+from\s+", label, maxsplit=1, flags=re.I)[0]
            rows.append({"overall": int(overall), "round": int(rnd), "pick": int(pick), "owner": canonical(owner), "compensatory": comp})
    else:
        start = text.find("## Round 1")
        end = text.find("## Related Content", start)
        body = text[start:end if end > start else None]
        rx = re.compile(r"^L\d+:\s*(\d+)[\.)]\s+(.+?)\s*$", re.M)
        for n, label in rx.findall(body):
            overall = int(n)
            if overall > EXPECTED[year]:
                continue
            comp = "compensatory" in label.lower()
            label = re.split(r"\s+\(", label, maxsplit=1)[0]
            label = re.split(r"\s+from\s+", label, maxsplit=1, flags=re.I)[0]
            rows.append({"overall": overall, "round": 1 if overall <= 32 else None, "pick": None, "owner": canonical(label), "compensatory": comp})
        for r in rows:
            r["round"] = ((r["overall"] - 1) // 32) + 1
            r["pick"] = r["overall"] - (r["round"] - 1) * 32
    rows.sort(key=lambda x: x["overall"])
    if [r["overall"] for r in rows] != list(range(1, EXPECTED[year] + 1)):
        raise ValueError(f"{year}: incomplete/duplicate overall sequence; got {len(rows)}")
    return rows


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", value.lower())


def parse_invitees_2021(text: str) -> list[dict]:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "Here are the invitees:")
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1) if line.startswith("--------------------------------------------------------------------------------"))
    school = None
    out = []
    for line in lines[start + 1:end]:
        if line.startswith("  * "):
            body = line[4:].strip()
            parts = [p.strip() for p in body.split(",")]
            name = parts[0]
            if len(parts) >= 2:
                position = parts[1]
                name = re.sub(r"\s+(?:QB|WR|RB|TE|DE|DT|OG|OT|OLB|ILB|CB|S|C|K|P|LS|FB)$", "", name)
            else:
                m = re.search(r"\s+(QB|WR|RB|TE|DE|DT|OG|OT|OLB|ILB|CB|S|C|K|P|LS|FB)$", name)
                if not m:
                    raise ValueError(f"Missing published position in invitee line: {body}")
                position = m.group(1)
                name = name[:m.start()].strip()
            if len(parts) >= 3 and norm(parts[-1]) == norm(school or ""):
                parts.pop()
            out.append({"name": name, "school": school, "position": position, "key": norm(name) + "|" + norm(school or "")})
        elif line.strip() and not line.startswith(("#", "http")):
            school = line.strip()
    if len(out) != 323:
        raise ValueError(f"Expected 323 invitees, parsed {len(out)}")
    return out


def main() -> None:
    sources = []
    all_rows = {}
    for year, meta in META.items():
        path = RAW / f"nfl_draft_order_{year}_webtext.txt"
        raw = path.read_bytes()
        rows = parse(year, raw.decode("utf-8"))
        owner_seq = ",".join(r["owner"] for r in rows).encode()
        source = {"year": year, **meta, "cachePath": f"data/raw/{path.name}",
                  "cacheFormat": "verbatim text returned by official-page web extraction; not original HTTP bytes",
                  "cacheSha256": hashlib.sha256(raw).hexdigest(), "ownerSequenceSha256": hashlib.sha256(owner_seq).hexdigest(),
                  "pickCount": len(rows), "usableForPreDraftOwnership": meta["usable"]}
        sources.append(source)
        all_rows[str(year)] = rows
    # Compare pre-draft owner sequence to the team that actually made each pick.
    # These differences are post-cutoff movement evidence, not owner-source errors.
    team_map = {"GNB":"GB", "KAN":"KC", "NOR":"NO", "SFO":"SF", "NWE":"NE", "OAK":"LV",
                "RAM":"LAR", "TAM":"TB", "SDG":"LAC", "RAI":"LV", "PHO":"ARI", "STL":"LAR"}
    actual = {}
    with (RAW / "draft_picks.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            y = int(r["season"])
            if 2020 <= y <= 2024:
                actual.setdefault(y, {})[int(r["pick"])] = team_map.get(r["team"], r["team"])
    post_draft_owner_changes = {}
    for y in range(2020, 2025):
        changed = []
        for r in all_rows[str(y)]:
            selected_by = actual[y].get(r["overall"])
            if selected_by and selected_by != r["owner"]:
                changed.append({"overall": r["overall"], "preDraftOwner": r["owner"], "selectedBy": selected_by})
        post_draft_owner_changes[str(y)] = {"count": len(changed), "examples": changed[:12], "all": changed}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    invite_path = RAW / "nfl_2021_combine_invitees_giants_webtext.txt"
    invite_raw = invite_path.read_bytes()
    invitees = parse_invitees_2021(invite_raw.decode("utf-8"))
    combine = {}
    with (RAW / "combine.csv").open(newline="", encoding="utf-8") as f:
        for line_number, r in enumerate(csv.DictReader(f), start=2):
            if int(r["season"]) == 2021:
                r["_sourceLine"] = line_number
                combine.setdefault(norm(r["player_name"]) + "|" + norm(r["school"]), []).append(r)
    matches, unmatched, ambiguous, official_invitees = [], [], [], []
    for invitee in invitees:
        candidates = combine.get(invitee["key"], [])
        if len(candidates) == 1:
            c = candidates[0]
            measurements = {k: c.get(k, "") or None for k in ("ht", "wt", "forty", "bench", "vertical", "broad_jump", "cone", "shuttle")}
            match = {"rawCombineCsvLine": int(c["_sourceLine"]), "rawName": c["player_name"], "rawSchool": c["school"],
                     "rawPosition": c["pos"], "pfrId": c["pfr_id"] or None, "measurements": measurements}
            matches.append({**invitee, "measurementMatch": match})
            official_invitees.append({**invitee, "eligibilitySource": "official-2021-combine-invitee-list", "sourceUrl": "https://www.giants.com/news/2021-nfl-scouting-combine-list-of-invited-prospects-new-format-nfl-draft", "sourcePublished": "2021-03-04T09:09:00", "measurementMatch": match})
        elif not candidates:
            unmatched.append(invitee)
            official_invitees.append({**invitee, "eligibilitySource": "official-2021-combine-invitee-list", "sourceUrl": "https://www.giants.com/news/2021-nfl-scouting-combine-list-of-invited-prospects-new-format-nfl-draft", "sourcePublished": "2021-03-04T09:09:00", "measurementMatch": None})
        else:
            ambiguous.append({**invitee, "candidateCount": len(candidates), "candidates": [{"name": r["player_name"], "school": r["school"]} for r in candidates]})
            official_invitees.append({**invitee, "eligibilitySource": "official-2021-combine-invitee-list", "sourceUrl": "https://www.giants.com/news/2021-nfl-scouting-combine-list-of-invited-prospects-new-format-nfl-draft", "sourcePublished": "2021-03-04T09:09:00", "measurementMatch": None})
    invitees_2021 = {
        "url": "https://www.giants.com/news/2021-nfl-scouting-combine-list-of-invited-prospects-new-format-nfl-draft",
        "publisher": "New York Giants (official NFL club site)", "published": "2021-03-04T09:09:00", "modified": None, "statedInviteeCount": 323,
        "cachePath": f"data/raw/{invite_path.name}", "cacheFormat": "verbatim text returned by official-team-page web extraction; not original HTTP bytes",
        "cacheSha256": hashlib.sha256(invite_raw).hexdigest(), "parsedCount": len(invitees),
        "matchingRule": "unique exact NFKD/lowercase/alphanumeric normalized player_name + school; no fuzzy matching or school aliases",
        "matchedCount": len(matches), "matchedWithoutPfrId": [r for r in matches if not r["measurementMatch"]["pfrId"]],
        "canonicalPfrIdCount": sum(bool(r["measurementMatch"]["pfrId"]) for r in matches),
        "unmatchedCount": len(unmatched), "ambiguousCount": len(ambiguous),
        "reconciledToCombineCsv": not unmatched and not ambiguous,
        "eligibleCount": len(official_invitees),
        "officialInvitees": official_invitees,
        "auditableEligibleList": official_invitees,
        "matches": matches, "unmatched": unmatched, "ambiguous": ambiguous,
    }
    OUT.write_text(json.dumps({"version": "additional-order-sources-v1", "sources": sources, "ownersByYear": all_rows, "ownerDifferencesFromFinalSelection": post_draft_owner_changes, "invitees2021": invitees_2021}, indent=2) + "\n")
    print(json.dumps({"sources": [{"year": s["year"], "pickCount": s["pickCount"], "usable": s["usableForPreDraftOwnership"], "ownerSequenceSha256": s["ownerSequenceSha256"]} for s in sources]}, indent=2))


if __name__ == "__main__":
    main()
