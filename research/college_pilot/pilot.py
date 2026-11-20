"""Audit historical college data in memory and emit aggregate diagnostics."""
import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

DEFAULT_SCENARIO = Path(__file__).resolve().parents[2] / "data/processed/scenario-2018.json"
CFBD = "https://api.collegefootballdata.com"
BOX_PDF = (
    "https://s3.us-east-2.amazonaws.com/sidearm.nextgen.sites/soonersports.com/"
    "documents/2017/11/28/5462974.pdf?timestamp=20190624105857"
)


class RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_rows(path, params, token=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{CFBD}{path}?{urlencode(params)}", headers=headers)
    with build_opener(RejectRedirect()).open(request, timeout=30) as response:
        body = response.read()
    rows = json.loads(body)
    if not isinstance(rows, list):
        raise ValueError(f"Expected record array at {path}")
    return rows, hashlib.sha256(body).hexdigest()


def normalize(value):
    return "".join(
        c for c in unicodedata.normalize("NFKD", value.strip()).casefold() if c.isalnum()
    )


def conservative_eligibility(game, cutoff, year, team):
    if game["season"] != year or game["seasonType"] not in ("regular", "postseason"):
        return "wrong_season"
    if team not in {normalize(game["homeTeam"]), normalize(game["awayTeam"])}:
        return "wrong_team"
    if game["completed"] is not True or game["startTimeTBD"] is not False:
        return "no_confirmed_game"
    start = datetime.fromisoformat(game["startDate"])
    if start.tzinfo is None:
        return "no_timezone"
    # Require a full calendar day after the UTC date of kickoff. The date of
    # any historical provider correction remains unknown.
    if start.astimezone(timezone.utc).date() + timedelta(days=1) >= cutoff.date():
        return "too_close_or_after_cutoff"
    return "eligible_reconstruction"


def roster_crosswalk(rows, prospects, source_team, scenario_team):
    source_team = normalize(source_team)
    scenario_team = normalize(scenario_team)
    roster = defaultdict(set)
    names_by_id = defaultdict(set)
    for row in rows:
        if normalize(row["team"]) != source_team or not row["id"]:
            continue
        name = normalize(f'{row["firstName"]} {row["lastName"]}')
        provider_id = str(row["id"])
        roster[name].add(provider_id)
        names_by_id[provider_id].add(name)
    pool = [p for p in prospects if normalize(p["college"] or "") == scenario_team]
    pool_names = Counter(normalize(p["name"]) for p in pool)
    mapping = {}
    status = Counter()
    for prospect in pool:
        name = normalize(prospect["name"])
        candidates = roster[name]
        if not candidates:
            status["unmatched"] += 1
        elif len(candidates) != 1 or pool_names[name] != 1:
            status["ambiguous"] += 1
        else:
            provider_id = next(iter(candidates))
            if len(names_by_id[provider_id]) != 1:
                status["ambiguous"] += 1
                continue
            mapping[provider_id] = prospect["id"]
            status["provisional_name_team"] += 1
    return mapping, status


def audit_boxes(rows, eligible_ids, source_team, mapping):
    status = Counter()
    fingerprints = defaultdict(set)
    seen = {}
    for row in rows:
        if row["id"] not in eligible_ids:
            status["box_outside_date_gate"] += 1
            continue
        for team in row["teams"]:
            if normalize(team["team"]) != normalize(source_team):
                continue
            for category in team["categories"]:
                for metric in category["types"]:
                    for athlete in metric["athletes"]:
                        provider_id = str(athlete["id"])
                        if provider_id not in mapping:
                            status["unmatched_athlete_observations"] += 1
                            continue
                        value = str(athlete["stat"]).strip()
                        if athlete["stat"] is None or value in {"", "-", "--", "N/A"}:
                            status["missing_values"] += 1
                            continue
                        key = row["id"], provider_id, category["name"], metric["name"]
                        values = seen.setdefault(key, set())
                        values.add(value)
    for (game_id, provider_id, category, metric), values in seen.items():
        if len(values) != 1:
            status["conflicting_observations"] += 1
            continue
        status["usable_observations"] += 1
        fingerprints[mapping[provider_id]].add((game_id, category, metric, next(iter(values))))
    status["prospects_with_observations"] = len(fingerprints)
    return status, fingerprints


def disclosure_counts(pool, fingerprints):
    baseline = Counter(p["position"] for p in pool)
    with_school = Counter((p["position"], p["college"]) for p in pool)
    with_stats = Counter(
        (p["position"], frozenset(fingerprints.get(p["id"], ()))) for p in pool
    )
    return {
        "pool": len(pool),
        "position_singletons": sum(v == 1 for v in baseline.values()),
        "position_school_singletons": sum(v == 1 for v in with_school.values()),
        "position_exact_sample_profile_singletons": sum(v == 1 for v in with_stats.values()),
        "profile_bearing_position_singletons": sum(
            baseline[p["position"]] == 1 for p in pool if p["id"] in fingerprints
        ),
        "profile_bearing_position_school_singletons": sum(
            with_school[(p["position"], p["college"])] == 1
            for p in pool if p["id"] in fingerprints
        ),
        "profile_bearing_exact_profile_singletons": sum(
            with_stats[(p["position"], frozenset(fingerprints[p["id"]]))] == 1
            for p in pool if p["id"] in fingerprints
        ),
    }


def run_cfbd(scenario, cutoff, pool, token, team, scenario_team, year):
    if year >= scenario["metadata"]["draftYear"]:
        raise ValueError("Choose a college season before the draft year")
    hashes = {}
    fetched = datetime.now(timezone.utc).isoformat()

    def fetch(path, **params):
        rows, hashes[path] = request_rows(path, params, token)
        return rows

    games = fetch("/games", year=year, team=team, seasonType="both")
    game_status = {
        game["id"]: conservative_eligibility(game, cutoff, year, normalize(team))
        for game in games
    }
    if len(game_status) != len(games):
        raise ValueError("Duplicate game IDs in schedule")
    eligible_ids = {gid for gid, status in game_status.items() if status == "eligible_reconstruction"}
    roster = fetch("/roster", year=year, team=team)
    mapping, joins = roster_crosswalk(roster, pool, team, scenario_team)
    boxes = fetch("/games/players", year=year, team=team, seasonType="both")
    observations, fingerprints = audit_boxes(boxes, eligible_ids, team, mapping)
    return {
        "source": "CollegeFootballData.com",
        "fetched_at": fetched,
        "season": year,
        "source_team": team,
        "scenario_team": scenario_team,
        "response_sha256": hashes,
        "schedule": Counter(game_status.values()),
        "roster_joins": joins,
        "box_observations": observations,
        "identity_exposure": disclosure_counts(pool, fingerprints),
        "availability_basis": "Event-date reconstruction; original publication unverified",
    }


def run_public_box(pool, cutoff, path):
    pdf = path.read_bytes()
    content = subprocess.run(
        ["pdftotext", "-layout", "-", "-"], input=pdf, check=True, capture_output=True
    ).stdout.decode()
    header = re.search(r"Oklahoma vs Kansas \(([A-Z][a-z]{2} \d{2}, \d{4}) at", content)
    if not header:
        raise ValueError("Expected Oklahoma–Kansas box score")
    played = datetime.strptime(header[1], "%b %d, %Y").date()
    individual_final = content.split("Individual Statistics (Final)", 1)[1].split("\f", 1)[0]
    passing = individual_final.split("Passing", 1)[1].split("Receiving", 1)[0]
    receiving = individual_final.split("Receiving", 1)[1].split("Punting", 1)[0]
    defensive = content.split("# Kansas             Solo", 1)[1].split("\f", 1)[0]
    # Abbreviations are reviewed against team roster/participation and the
    # contemporaneous AP game story. The PDF and individual values stay local.
    sample = [
        ("Oklahoma", "Baker Mayfield", passing, r"(?m)^Mayfield, Baker\s+(\d+-\d+-\d+\s+\d+\s+\d+)"),
        ("Oklahoma", "Mark Andrews", receiving, r"(?m)^Andrews, Mark\s+(\d+\s+\d+\s+\d+)"),
        ("Oklahoma", "Dimitri Flowers", receiving, r"(?m)^Flowers, D\.\s+(\d+\s+\d+\s+\d+)"),
        ("Kansas", "Dorance Armstrong Jr.", defensive, r"(?m)^2 Armstrong,D\.\s+(\d+\s+\d+\s+\d+\s+\d+\.\d+-\d+)"),
    ]
    fingerprints = {}
    for college, name, section, pattern in sample:
        values = re.findall(pattern, section)
        matches = [p for p in pool if normalize(p["name"]) == normalize(name) and p["college"] == college]
        if len(values) != 1 or len(matches) != 1:
            raise ValueError("Reviewed sample row or eligible link no longer unique")
        fingerprints[matches[0]["id"]] = tuple(values[0].split())

    def passes_event_cutoff(test_cutoff):
        return played + timedelta(days=1) < test_cutoff

    # The game is an event-date proxy; primary archive URL is a later migration.
    cutoff_pass = passes_event_cutoff(cutoff.date())
    return {
        "source": BOX_PDF,
        "source_sha256": hashlib.sha256(pdf).hexdigest(),
        "game_date": played.isoformat(),
        "availability_basis": "Event-date reconstruction; one independently corroborated passing line",
        "reviewed_rows": len(sample),
        "exact_eligible_joins": len(fingerprints),
        "rows_passing_scenario_date_gate": len(fingerprints) if cutoff_pass else 0,
        "rows_passing_game_day_negative_control": len(fingerprints) if passes_event_cutoff(played) else 0,
        "identity_exposure": disclosure_counts(pool, fingerprints if cutoff_pass else {}),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("probe", "cfbd", "public-box"))
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--team", default="Oklahoma")
    parser.add_argument("--scenario-team", default="Oklahoma")
    parser.add_argument("--year", type=int, default=2017)
    parser.add_argument("--pdf", type=Path)
    args = parser.parse_args()
    token = os.getenv("CFBD_API_KEY", "").strip()
    if args.mode == "probe":
        try:
            rows, _ = request_rows("/stats/player/season", {"year": args.year, "team": args.team}, token)
        except HTTPError as error:
            print(json.dumps({"with_key": bool(token), "http_status": error.code}))
            return 1
        except URLError:
            parser.exit(1, "CFBD connection failed\n")
        print(json.dumps({"with_key": bool(token), "http_status": 200, "rows": len(rows)}))
        return 0
    raw = args.scenario.read_bytes()
    scenario = json.loads(raw)
    cutoff = datetime.fromisoformat(scenario["metadata"]["informationCutoff"]).astimezone(timezone.utc)
    pool = [p for p in scenario["prospects"] if p["playable"] is True]
    if args.mode == "public-box":
        if not args.pdf:
            parser.error("public-box requires --pdf with the linked official game document")
        result = run_public_box(pool, cutoff, args.pdf)
    else:
        if not token:
            parser.exit(1, "Set the organization-authorized CFBD_API_KEY in the environment\n")
        try:
            result = run_cfbd(scenario, cutoff, pool, token, args.team, args.scenario_team, args.year)
        except HTTPError as error:
            parser.exit(1, f"CFBD returned HTTP {error.code}\n")
        except URLError:
            parser.exit(1, "CFBD connection failed\n")
    result["scenario_sha256"] = hashlib.sha256(raw).hexdigest()
    result["cutoff"] = cutoff.isoformat()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
