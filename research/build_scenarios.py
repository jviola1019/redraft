"""Build audited research-alpha scenarios without draft-data leakage.

Pool scope and order evidence vary by year; the coverage manifest records the
known limits instead of treating provider data as complete by default.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
sys.path.insert(0, str(ROOT / "research"))
from clean import TEAMS, college, height, norm, num, position, tid  # noqa: E402
import audit_expansion  # noqa: E402
from audit_expansion import reverse_ownership  # noqa: E402

audit_expansion.DRAFT_DATES[2026] = ("04-23", "04-25")
SCENARIO_CUTOFFS = {
    2019: "2019-04-25T23:59:00Z", 2020: "2020-04-15T23:59:00Z",
    2021: "2021-04-29T23:59:00Z", 2022: "2022-04-28T23:59:00Z", 2023: "2023-04-27T23:59:00Z",
    2024: "2024-04-25T23:59:00Z", 2025: "2025-04-24T23:59:00Z",
    2026: "2026-04-22T23:59:00Z",
}
SCENARIO_VERSIONS = {year: f"nflverse-{year}-combine-pool-v1" for year in SCENARIO_CUTOFFS}
RAIDERS_RELEASE = "https://static.clubs.nfl.com/image/upload/raiders/zsb8qfkli33h2k8oqf1t.pdf"
COMBINE_SOURCE = "https://github.com/nflverse/nflverse-data/releases/tag/combine"
DRAFT_SOURCE = "https://github.com/nflverse/nflverse-data/releases/tag/draft_picks"
GAME_SOURCE = "https://github.com/nflverse/nflverse-data/releases/tag/schedules"
TRADE_SOURCE = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/trades.csv"
NFL_ORDER_2025 = "https://www.nfl.com/news/2025-nfl-draft-order-for-all-seven-rounds"
NFL_ORDER_2026 = "https://media.nfl.com/content/dam/communications/draft/2026/2026%20NFL%20Draft%20-%20Round-by-Round.pdf"
NFL_INVITES_2026 = "https://www.nfl.com/news/nfl-combine-full-list-of-draft-prospects-invited-to-2026-scouting-event"
ADDITIONAL_ORDERS_PATH = ROOT / "data" / "clean" / "additional_order_sources.json"
OFFICIAL_2025_ROUNDS = [
    "TEN CLE NYG NE JAX OAK NYJ CAR NO CHI SF DAL MIA IND ATL ARI CIN SEA TB DEN PIT LAC GB MIN HOU LAR BAL DET WAS BUF KC PHI",
    "CLE NYG TEN JAX OAK NE CHI NO CHI NYJ SF DAL IND ATL ARI MIA CIN SEA DEN SEA TB GB LAC BUF CAR HOU BAL DET WAS BUF KC PHI",
    "NYG KC CLE OAK NE JAX NO CHI NYJ CAR SF DAL NE ARI HOU IND CIN SEA PIT TB DEN LAC GB JAX HOU LAR BAL SEA NO CLE KC PHI MIN MIA NYG SF LAR DET",
    "TEN CLE NYG NE JAX OAK BUF NYJ CAR NO SF CAR ARI MIA IND ATL CIN TEN TB DEN PIT GB LAC JAX LAR WAS BAL DET NO BUF KC PHI MIA BAL SEA SF",
    "MIN CAR TEN JAX OAK NE NYJ CAR SF CHI DAL MIA IND ARI CIN NYG MIA PIT TB LAC GB SF PHI NYJ CAR PHI PHI CLE TEN PHI BUF BUF NE SEA BUF DAL SEA BAL",
    "BUF TEN HOU OAK LAC JAX BAL NO PIT NYJ MIN TEN IND LAR DEN CLE CIN JAX LAR DET DEN GB LAC CLE LAR LAR BAL DAL WAS BUF NYJ DEN LAC BAL DAL BAL OAK LAC OAK HOU",
    "DAL ATL NYG NE JAX OAK SEA MIA ARI KC SF DET PIT CAR MIA IND CHI SEA TB HOU GB NE DAL CHI HOU ATL BAL DET WAS NYG DAL NO SF GB KC SF MIA NO HOU LAC KC",
]
OFFICIAL_2025_COMPENSATORY = (set(range(97, 103)) | set(range(135, 139)) |
                              set(range(169, 177)) | set(range(209, 217)) |
                              set(range(249, 258)))

# NFL Football Operations PDF, "2026 NFL Draft ... as of April 22, 2026".
# Team names are in overall-pick order; these codes are franchise IDs.
OFFICIAL_2026_ROUNDS = [
    "OAK NYJ ARI TEN NYG CLE WAS NO KC NYG MIA DAL LAR BAL TB NYJ DET MIN CAR DAL PIT LAC PHI CLE CHI BUF SF HOU KC MIA NE SEA",
    "NYJ ARI TEN OAK NYG HOU CLE KC CIN NO MIA NYJ BAL TB IND ATL MIN DET CAR GB PIT PHI LAC JAX CHI SF HOU CHI LAR DEN NE SEA",
    "ARI TEN OAK PHI HOU CLE WAS CIN NO KC MIA PIT TB IND ATL BAL JAX MIN CAR GB PIT LAC MIA JAX CHI MIA BUF DAL LAR MIA NE SEA MIN PHI PIT JAX",
    "TEN OAK NYJ ARI NYG HOU CLE DEN KC CIN DEN DAL IND PHI BAL TB OAK DET CAR GB PIT ATL LAC JAX NE BUF SF DET CHI MIA NE NO SF OAK PIT NO PHI SF SF NYJ",
    "HOU TEN ARI TEN NYG CLE WAS KC CLE NO MIA DAL GB BAL TB IND DET CAR CAR GB PIT BAL MIN JAX BUF JAX HOU BUF KC DEN NE NO BAL BAL OAK KC DAL PHI NYJ DAL DET",
    "BUF ARI TEN OAK NYG WAS SEA CIN NO NE NYG NYG TEN TB MIN PHI NE CIN CAR GB NE JAX LAC DET CLE LAR OAK WAS KC BAL NE DET IND ATL PIT",
    "ARI DAL OAK BUF CIN DET WAS PIT TEN CIN MIA NYJ TB PIT ATL LAR JAX MIN MIN GB PIT MIA CHI JAX CHI NYJ HOU MIN JAX DEN NE CLE IND BAL LAR LAR BAL IND GB DEN DEN",
]
OFFICIAL_2026_COMPENSATORY = (set(range(97, 101)) | set(range(133, 141)) |
                              set(range(173, 182)) | set(range(214, 217)) |
                              set(range(249, 258)))


def read_csv(filename: str) -> list[dict[str, str]]:
    with (RAW / filename).open(newline="") as handle:
        return list(csv.DictReader(handle))


def player_id(year: int, name: str, school: str) -> str:
    key = f"{norm(name)}|{college(school)}".encode()
    return f"p{year}-" + hashlib.sha256(key).hexdigest()[:10]


def school_match_key(year: int, school: str) -> str:
    # 2021 invitee-to-draft identity matching uses literal normalized school
    # names only; the general historical alias map would make that join fuzzy.
    return norm(school) if year == 2021 else college(school)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def historical_teams(games: list[dict[str, object]], year: int) -> list[dict[str, object]]:
    result = []
    for code, name, conference, division in TEAMS:
        if year >= 2020 and code == "OAK":
            name = "Las Vegas Raiders"
        if year == 2021 and code == "WAS":
            name = "Washington Football Team"
        if year >= 2022 and code == "WAS":
            name = "Washington Commanders"
        played = [g for g in games if g["season"] == year - 1 and g["type"] == "REG"
                  and code in (g["home"], g["away"])]
        # The context year is the season before the draft-year scenario.
        expected = 17 if (year - 1) >= 2021 else 16
        # The 2022 Buffalo–Cincinnati game was cancelled and not replayed.
        if year == 2023 and code in {"BUF", "CIN"}:
            expected = 16
        if len(played) != expected:
            raise ValueError(f"{year - 1} context for {code} has {len(played)} games, expected {expected}")
        wins = losses = ties = points_for = points_against = 0
        for game in played:
            ours = game["homeScore"] if game["home"] == code else game["awayScore"]
            theirs = game["awayScore"] if game["home"] == code else game["homeScore"]
            points_for += int(ours)
            points_against += int(theirs)
            wins += int(ours > theirs)
            losses += int(ours < theirs)
            ties += int(ours == theirs)
        result.append({"id": code, "name": name, "conference": conference,
                       "division": division, "priorWins": wins,
                       "priorLosses": losses, "priorTies": ties,
                       "priorPointsFor": points_for,
                       "priorPointsAgainst": points_against})
    return result


def build_scenario(year: int) -> tuple[dict[str, object], dict[str, object]]:
    if year not in SCENARIO_CUTOFFS:
        raise ValueError(f"No audited builder for {year}")
    cutoff = SCENARIO_CUTOFFS[year]
    version = SCENARIO_VERSIONS[year]
    combines = [r for r in read_csv("combine.csv") if r["season"] == str(year)]
    provider_combines = combines
    drafts = [r for r in read_csv("draft_picks.csv") if r["season"] == str(year)]
    raw_games = read_csv("games.csv")
    raw_trades = read_csv("trades.csv")
    order_cache = json.loads(ADDITIONAL_ORDERS_PATH.read_text()) if ADDITIONAL_ORDERS_PATH.exists() else {"sources": [], "ownersByYear": {}}
    extra_source = next((s for s in order_cache["sources"] if s["year"] == year), None)
    extra_owner_rows = order_cache.get("ownersByYear", {}).get(str(year), [])
    invitee_audit = order_cache.get("invitees2021") if year == 2021 else None
    if year == 2021:
        if not invitee_audit or len(invitee_audit.get("officialInvitees", [])) != 323:
            raise ValueError("2021 official invitee roster must contain exactly 323 audited names")
        by_pair = {(norm(r["player_name"]), college(r["school"])): r for r in provider_combines}
        combines = []
        for invitee in invitee_audit["officialInvitees"]:
            measurement = invitee.get("measurementMatch")
            pair = (norm(invitee["name"]), college(invitee["school"]))
            row = by_pair.get(pair) if measurement else None
            # The invitee roster independently establishes eligibility. Provider
            # measurements are attached only through the audited exact pair.
            measures = measurement.get("measurements", {}) if measurement else {}
            combines.append({
                "season": "2021", "player_name": invitee["name"], "school": invitee["school"],
                "pos": (row["pos"] if row else (measurement.get("rawPosition") if measurement else invitee.get("position", ""))),
                "ht": measures.get("ht"), "wt": measures.get("wt"), "forty": measures.get("forty"),
                "bench": measures.get("bench"), "vertical": measures.get("vertical"),
                "broad_jump": measures.get("broad_jump"), "cone": measures.get("cone"),
                "shuttle": measures.get("shuttle"), "pfr_id": (measurement.get("pfrId", "") if measurement else ""),
            })
    if not combines or not drafts:
        raise ValueError(f"{year} combine or draft source has no rows")

    draft_rows = sorted(drafts, key=lambda r: int(r["pick"]))
    numbers = [int(r["pick"]) for r in draft_rows]
    if numbers != list(range(1, len(draft_rows) + 1)):
        raise ValueError(f"{year} actual draft picks are not unique, sequential overall slots")
    if year == 2025:
        from audit_expansion import corrected_2025
        raw_trades = corrected_2025(raw_trades)
    ownership = reverse_ownership(year, draft_rows, raw_trades)
    has_primary_order = bool(extra_source and extra_source.get("usableForPreDraftOwnership"))
    if ownership["issues"] and not has_primary_order:
        raise ValueError(f"{year} trade reversal has unresolved issues: {ownership['issues'][:3]}")
    owners = {int(number): team for number, team in ownership["candidateOwners"].items()}
    reversal_mismatches: list[dict[str, object]] = []
    primary_order_snapshot_sha256 = None
    compensatory_slots: set[int] | None = None
    if has_primary_order:
        official_codes = [tid(row["owner"]) for row in extra_owner_rows]
        if len(official_codes) != len(draft_rows):
            raise ValueError(f"{year} primary order has {len(official_codes)} rows, provider has {len(draft_rows)}")
        official_owners = dict(enumerate(official_codes, 1))
        reversal_mismatches = [{"overall": number, "reversed": owners[number], "official": official_owners[number]}
                               for number in numbers if owners[number] != official_owners[number]]
        owners = official_owners
        compensatory_slots = {int(row["overall"]) for row in extra_owner_rows if row.get("compensatory")}
        primary_order_snapshot_sha256 = extra_source["ownerSequenceSha256"]
    elif year == 2025:
        # The official NFL page was updated before Round 1. Apply the verified
        # Browns–Texans trade made on draft day before the first selection.
        for asset in raw_trades:
            if asset["trade_id"] == "1918" and asset["pick_season"] == "2025":
                owners[int(asset["pick_number"])] = tid(asset["received"])
        official_codes = [tid(code) for round_codes in OFFICIAL_2025_ROUNDS for code in round_codes.split()]
        if len(official_codes) != len(draft_rows):
            raise ValueError(f"2025 official NFL order has {len(official_codes)} slots, provider has {len(draft_rows)}")
        official_owners = dict(enumerate(official_codes, 1))
        primary_order_snapshot_sha256 = hashlib.sha256(
            json.dumps(official_codes, separators=(",", ":")).encode()).hexdigest()
        reversal_mismatches = [{"overall": number, "reversed": owners[number], "official": official_owners[number]}
                               for number in numbers if owners[number] != official_owners[number]]
        owners = official_owners
        compensatory_slots = OFFICIAL_2025_COMPENSATORY
    elif year == 2026:
        official_codes = [tid(code) for round_codes in OFFICIAL_2026_ROUNDS for code in round_codes.split()]
        if len(official_codes) != len(draft_rows):
            raise ValueError(f"2026 official NFL order has {len(official_codes)} slots, provider has {len(draft_rows)}")
        official_owners = dict(enumerate(official_codes, 1))
        primary_order_snapshot_sha256 = hashlib.sha256(
            json.dumps(official_codes, separators=(",", ":")).encode()).hexdigest()
        reversal_mismatches = [{"overall": number, "reversed": owners[number], "official": official_owners[number]}
                               for number in numbers if owners[number] != official_owners[number]]
        # The NFL Operations order is explicitly as of April 22, before the draft.
        owners = official_owners
        compensatory_slots = OFFICIAL_2026_COMPENSATORY
    if set(owners) != set(numbers):
        raise ValueError(f"{year} reversed owner slots do not match the actual selection slots")
    if set(owners.values()) != {team[0] for team in TEAMS}:
        raise ValueError(f"{year} initial owner set does not cover exactly 32 franchises")

    # Keep only season game records; later actual outcomes remain isolated in the
    # history field and are never copied into prospect predictors.
    games = [{"id": r["game_id"], "season": int(r["season"]), "type": r["game_type"],
              "week": int(r["week"]), "date": r["gameday"],
              "home": tid(r["home_team"]), "away": tid(r["away_team"]),
              "homeScore": int(r["home_score"]), "awayScore": int(r["away_score"])}
             for r in raw_games
             if year - 1 <= int(r["season"]) <= year + 5
             and r["home_score"] and r["away_score"]]
    teams = historical_teams(games, year)

    prospects: list[dict[str, object]] = []
    identities: dict[str, str] = {}
    by_pfr: dict[str, str] = {}
    by_name_school: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for row in sorted(combines, key=lambda r: (norm(r["player_name"]), college(r["school"]))):
        ident = player_id(year, row["player_name"], row["school"])
        if ident in identities:
            raise ValueError(f"{year} combine ID collision: {ident}")
        pfr = row["pfr_id"]
        if pfr and pfr in by_pfr:
            raise ValueError(f"{year} combine PFR ID reused: {pfr}")
        identities[ident] = pfr
        by_name_school[norm(row["player_name"]), school_match_key(year, row["school"])].append(ident)
        if pfr:
            by_pfr[pfr] = ident
        prospects.append({
            "id": ident, "name": row["player_name"],
            "position": position(row["pos"]), "college": row["school"],
            "heightIn": height(row["ht"]), "weightLb": num(row["wt"]),
            "forty": num(row["forty"]), "bench": num(row["bench"]),
            "verticalIn": num(row["vertical"]), "broadJumpIn": num(row["broad_jump"]),
            "cone": num(row["cone"]), "shuttle": num(row["shuttle"]),
            "source": (invitee_audit["url"] if invitee_audit else COMBINE_SOURCE), "availableBy": cutoff,
            "availabilityBasis": ("Named on the official 2021 invitee roster; eligibility does not require a provider measurement match" if year == 2021 else "Recorded combine participant; historical per-measurement publication timestamps unavailable"),
            "eligibilitySource": "combine-participant",
            "eligibilityProvenance": ("Official NFL 2021 invitee list; COVID-era combine invitee eligibility. Measurements join only on unique exact normalized name+school." if year == 2021 else "nflverse combine participant row; pool restricted to recorded combine participants"),
            "playable": True,
        })

    # Draft records are reference-only identity supplements.  Do not project
    # round, slot, team, career totals, or outcomes into the pre-draft pool.
    actual: list[dict[str, object]] = []
    seen_pfr: set[str] = set()
    used_ids = {p["id"] for p in prospects}
    for row in draft_rows:
        pfr = row["pfr_player_id"]
        if not pfr:
            raise ValueError(f"{year} actual pick {row['pick']} lacks a stable PFR identity")
        if pfr in seen_pfr:
            raise ValueError(f"{year} draft source repeats PFR identity {pfr}")
        seen_pfr.add(pfr)
        ident = by_pfr.get(pfr)
        if ident is None:
            candidates = by_name_school.get((norm(row["pfr_player_name"]), school_match_key(year, row["college"])), [])
            if len(candidates) == 1:
                ident = candidates[0]
        if ident is None:
            if year == 2021:
                # Keep an identity unresolved when a school alias would be needed
                # to join it to an eligible invitee.
                key = f"{norm(row['pfr_player_name'])}|{norm(row['college'] or '')}".encode()
                ident = f"p{year}-ref-" + hashlib.sha256(key).hexdigest()[:10]
            else:
                ident = player_id(year, row["pfr_player_name"], row["college"] or "")
            if ident in used_ids:
                raise ValueError(f"{year} reference-only identity collides with combine player: {ident}")
            used_ids.add(ident)
            prospects.append({
                "id": ident, "name": row["pfr_player_name"],
                "position": position(row["position"]),
                "college": row["college"] or "Not reported",
                "heightIn": None, "weightLb": None, "forty": None,
                "bench": None, "verticalIn": None, "broadJumpIn": None,
                "cone": None, "shuttle": None, "source": DRAFT_SOURCE,
                "availableBy": cutoff,
                "availabilityBasis": "Retrospective identity only; not available in the playable pool",
                "eligibilitySource": "retrospective-draft-record",
                "playable": False,
            })
        actual.append({"overall": int(row["pick"]), "round": int(row["round"]),
                       "team": tid(row["team"]), "prospectId": ident})

    picks = []
    for number in numbers:
        item = {"overall": number,
                "round": int(next(r["round"] for r in draft_rows if int(r["pick"]) == number)),
                "owner": owners[number]}
        if compensatory_slots is not None:
            item["compensatory"] = number in compensatory_slots
        picks.append(item)
    if len(picks) != len(drafts) or len(actual) != len(drafts):
        raise ValueError(f"{year} slot count changed; re-audit the current source")
    if len({p["prospectId"] for p in actual}) != len(actual):
        raise ValueError("2019 actual selections do not resolve uniquely")

    file_sources = {
        "data/raw/combine.csv": COMBINE_SOURCE,
        "data/raw/draft_picks.csv": DRAFT_SOURCE,
        "data/raw/games.csv": GAME_SOURCE,
        "data/raw/trades.csv": TRADE_SOURCE,
    }
    if extra_source:
        file_sources[extra_source["cachePath"]] = {"url": extra_source["url"],
                                                   "cacheSha256": extra_source["cacheSha256"],
                                                   "cacheFormat": extra_source["cacheFormat"],
                                                   "ownerSequenceSha256": extra_source.get("ownerSequenceSha256")}
        file_sources["data/clean/additional_order_sources.json"] = "normalized third-party source audit artifact"
    if invitee_audit:
        file_sources[invitee_audit["cachePath"]] = {
            "url": invitee_audit["url"], "cacheSha256": invitee_audit["cacheSha256"],
            "cacheFormat": invitee_audit["cacheFormat"], "parsedInvitees": invitee_audit["parsedCount"]}
        file_sources["data/clean/additional_order_sources.json"] = "normalized official invitee and order audit artifact"
    metadata = {
        "version": version, "draftYear": year, "informationCutoff": cutoff,
        "verifiedDate": datetime.now(timezone.utc).date().isoformat(),
        "informationCutoffConfidence": "reconstructed; original combine measurement timestamps unavailable",
        "playableProspectCount": len(combines),
        "referenceOnlyProspectCount": len(prospects) - len(combines),
        "poolDefinition": ("Official 2021 NFL Combine invitee roster (COVID-era event); provider measurements joined only by unique exact normalized name+school" if year == 2021 else "Recorded combine participants only; not a complete draft-eligible population"),
        "poolWarning": ("The complete 323-name official 2021 invitee list defines eligibility. 182 have an exact name/school measurement-row join; 141 have no provider row, and individual measurement fields can also be missing." if year == 2021 else f"Only {year} combine rows are playable. Non-combine eligible and undrafted players are not represented; do not interpret as a complete scouting pool."),
        "missingFields": ((["provider measurements for 141 official invitees without an exact name/school row"] if year == 2021 else
                           [f"individual name/school reconciliation to {year} official invitee roster"]) +
                          ["college-season production", "pre-draft injury history", "complete pre-draft rosters",
                           "contracts and cap", "contemporaneous scouting grades"]),
        "officialInviteeSource": invitee_audit["url"] if invitee_audit else None,
        "officialInviteeCount": invitee_audit["parsedCount"] if invitee_audit else None,
        "officialInviteeMeasurementJoin": ({"joinRule": invitee_audit["matchingRule"],
                                            "exactNameSchoolMatches": invitee_audit["matchedCount"],
                                            "missingProviderMeasurements": invitee_audit["unmatchedCount"],
                                            "ambiguousMatches": invitee_audit["ambiguousCount"],
                                            "pfrIdNotRequiredForEligibility": True}
                                           if invitee_audit else None),
        "orderSource": (TRADE_SOURCE if year == 2021 else (extra_source["url"] if extra_source else
                        (RAIDERS_RELEASE if year == 2019 else (NFL_ORDER_2025 if year == 2025 else NFL_ORDER_2026)))),
        "orderSourceRejectedAsOfEvidence": ({"url": extra_source["url"], "published": extra_source.get("published"),
                                              "reason": extra_source.get("cutoffEvidence")}
                                             if year == 2021 and extra_source else None),
        "primaryOrderOwnerSequenceSha256": primary_order_snapshot_sha256,
        "primaryOrderOwnerMismatchCountBeforeOverride": len(reversal_mismatches),
        "primaryOrderSourceRecord": extra_source,
        "orderPublished": (None if year == 2021 else (extra_source.get("published") if extra_source else
                           (None if year == 2019 else
                            ("2025-03-11T20:51:00-04:00" if year == 2025 else None)))),
        "orderModified": (extra_source.get("modified") if extra_source else
                          ("2025-04-24T17:15:00-04:00" if year == 2025 else None)),
        "orderAsOf": (None if year == 2021 else (extra_source.get("asOf") if extra_source else
                      (None if year == 2019 else
                       ("Beginning of Round 1, 2025" if year == 2025 else "As of April 22, 2026")))),
        "orderVerification": ("Pre-draft owners are reconstructed by reversing nflverse draft-day transactions; reversal audit has zero unresolved issues. No complete contemporaneous primary order comparison is claimed." if year == 2021 else
                              (f"Owner sequence comes from the contemporaneous primary order source; reversal comparison differed at {len(reversal_mismatches)} picks. Primary source sequence is authoritative." if extra_source and has_primary_order else
                              ("Draft-day trade reversal has no source inconsistencies; the Raiders release documents club pre-draft slots, but a full leaguewide row comparison is unavailable." if year == 2019 else
                               (f"Reversed transaction owners compared to NFL.com list accurate at Round 1; {len(reversal_mismatches)} rows differed before applying the primary order." if year == 2025 else
                                f"nflverse trade reversal compared with NFL Operations April 22 primary order; {len(reversal_mismatches)} rows differed before applying the primary order.")))),
        "orderWarning": ("Reverse-transaction ownership is audited with zero unresolved issues; no strict archived pre-draft order snapshot is available. An NFL.com page published March 19 contains a later trade and is explicitly excluded as an as-of source." if year == 2021 else
                         (extra_source["cutoffEvidence"] if extra_source and has_primary_order else
                         ("2019 owners are reconstructed from nflverse transactions without a complete leaguewide primary-order row check." if year == 2019 else
                          ("Owners are the NFL.com primary order as of Round 1; trade data mismatches are retained in audit metadata." if year == 2025 else
                           "Owners are the NFL Football Operations primary order as of April 22; trade-data mismatches are retained in audit metadata.")))),
        "compensatoryClassification": "Exact compensatory flags from official order sources for 2020, 2022, 2023, 2024, 2025, and 2026; unknown for 2019 and 2021.",
        "attribution": "Factual data from nflverse (combine, draft selections, games) and nflverse/nfldata (transactions); official NFL/Raiders pages used for source checks. No logos or photos used.",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "sourceFiles": [{"path": name, "url": url, "sha256": digest(ROOT / name)}
                        for name, url in file_sources.items()],
        "referenceIsolation": "actualPicks and post-cutoff games are historical references only; neither is included in prospect features",
    }
    if year == 2026:
        metadata["officialInviteeSource"] = NFL_INVITES_2026
        metadata["officialInviteeCount"] = 319
        metadata["officialInviteeAudit"] = "NFL source reports 319 invitees; nflverse has 319 combine rows. Counts agree, but individual name/school matches are not stored."
    dataset = {"metadata": metadata, "teams": teams, "prospects": prospects,
               "picks": picks, "actualPicks": actual, "games": games}
    checks = {
        "draftSlots": len(picks), "slotNumbersSequential": [p["overall"] for p in picks] == list(range(1, len(picks) + 1)),
        "reversedOwnershipIssues": len(ownership["issues"]),
        "officialOrderMismatchesBeforePrimaryOverride": len(reversal_mismatches),
        "officialOrderMismatchesAfterOverride": 0 if year in {2025, 2026} else None,
        "initialOwnerFranchises": len(set(owners.values())),
        "combinePoolRows": len(combines), "referenceOnlyRows": len(prospects) - len(combines),
        "actualSelectionsResolved": len(actual), "duplicateActualSelections": len(actual) - len({p["prospectId"] for p in actual}),
        "completedGamesBySeason": dict(sorted(collections.Counter(g["season"] for g in games).items())),
    }
    report = {
        "year": year, "status": "research-alpha-dataset-built", "dataset": f"data/processed/scenario-{year}.json",
        "datasetVersion": version, "cutoff": cutoff, "checks": checks,
        "ownershipMethod": "Reverse grouped draft-day trades using research/audit_expansion.py reverse_ownership.",
        "ownershipDisagreements": ownership["issues"],
        "reversalVsOfficialMismatches": reversal_mismatches,
        "limitations": [metadata["poolWarning"], metadata["orderWarning"], metadata["compensatoryClassification"],
                        "Historical games after the cutoff are included as reference labels and must never be exposed as pre-draft features."],
        "statusReason": "Pre-draft order and combine-participant pool are available for research-alpha gameplay; full eligible population and strict archival availability remain unsupported.",
    }
    return dataset, report


def coverage_manifest(report: dict[str, object]) -> dict[str, object]:
    years = []
    for year in range(2018, 2027):
        if year == 2018:
            years.append({"year": year, "status": "existing-research-alpha",
                          "dataset": "data/processed/scenario-2018.json",
                          "blockers": ["Combine-only pool is incomplete", "Strict original publication timestamps unavailable"]})
        elif year in SCENARIO_CUTOFFS:
            current = next(r for r in report if r["year"] == year)
            years.append({"year": year, "status": current["status"], "dataset": current["dataset"],
                          "blockers": current["limitations"]})
        elif year == 2021:
            years.append({"year": year, "status": "blocked-eligibility-audit",
                          "evidence": {"combineRows": 464, "officialInviteesReported": 323,
                                       "officialSource": "https://www.giants.com/news/2021-nfl-scouting-combine-list-of-invited-prospects-new-format-nfl-draft",
                                       "parsedInvitees": 323, "exactNameSchoolMatches": 182,
                                       "matchesWithCanonicalPfrId": 165, "matchesWithoutCanonicalPfrId": 17,
                                       "unmatchedInvitees": 141, "ambiguousMatches": 0,
                                       "matchingRule": "unique exact normalized player name + school; no fuzzy matching or aliases"},
                          "blockers": ["Only 182 of 323 official invitees have an exact name and school match; 17 matched rows lack canonical PFR IDs and 141 have no exact provider match", "The 464 provider measurement rows are not a complete invitee-derived playable pool", "Do not fill the missing eligible pool with actual draft selections"]})
        elif year == 2025:
            years.append({"year": year, "status": "blocked-compensatory-slot-classification",
                          "evidence": {"selections": 257, "combineRows": 329,
                                       "officialOrder": "https://www.nfl.com/news/2025-nfl-draft-order-for-all-seven-rounds"},
                          "blockers": ["audit_expansion.py explicit corrections remove 10 raw trade-reversal issues, but a reproducible slot-by-slot comparison with the NFL.com primary order page has not been saved as a source artifact", "The draft-picks file does not identify exact compensatory slots; do not infer them from order position", "The 329 combine rows have not been school-aware reconciled to the official invite list"]})
        elif year == 2026:
            years.append({"year": year, "status": "blocked-incomplete-observation-and-order",
                          "blockers": ["2026 season observations are incomplete at the November 12, 2026 planning date", "No complete checked-in pre-draft owner order and eligible-pool audit", "Five-season outcome labels cannot exist yet"]})
        elif year == 2020:
            years.append({"year": year, "status": "blocked-ownership-and-eligibility-audit",
                          "blockers": ["Raw reversal has two receiver mismatches for pick 117 on April 23, 2020 (trade IDs 1485 and 1483; MIN/SF/TB chain); no primary-source correction verified", "No complete school-aware official invitee roster audit is checked in", "Do not derive a full pool from actual draft selections"]})
        elif year == 2022:
            years.append({"year": year, "status": "blocked-ownership-and-eligibility-audit",
                          "blockers": ["Raw reversal has nine issues: pick 255 trade 1683; 261/1681; 235 receiver mismatch trade 1676; picks 198/1674, 169/1671, 149/1669, 124/1660, 59/1656, and 166/1649", "No audited source corrections or full official invitee roster match", "Do not derive a full pool from actual draft selections"]})
        elif year == 2023:
            years.append({"year": year, "status": "blocked-ownership-and-eligibility-audit",
                          "blockers": ["Raw reversal has four issues: pick 248 trade 1773; pick 168/1759; pick 139 receiver mismatch trade 1752; pick 230 receiver mismatch trade 1751", "No audited source corrections or full official invitee roster match", "Do not derive a full pool from actual draft selections"]})
        elif year == 2024:
            years.append({"year": year, "status": "blocked-ownership-and-eligibility-audit",
                          "blockers": ["Raw reversal has seven issues: pick 190/1863, 176/1858, 173 receiver mismatch trade 1848, 155/1847, 53/1845, and pick 32 receiver mismatches in trades 1839 and 1838", "No audited source corrections or full official invitee roster match", "Do not derive a full pool from actual draft selections"]})
        else:
            years.append({"year": year, "status": "blocked-no-primary-order-audit",
                          "blockers": ["No checked-in year-specific audit compares reconstructed ownership with a primary pre-draft order", "No school-aware invitee-to-combine audit", "Do not enable a scenario from provider rows alone"]})
    combine_rows = read_csv("combine.csv")
    draft_rows = read_csv("draft_picks.csv")
    game_rows = read_csv("games.csv")
    observed_inputs = []
    for year in range(2018, 2027):
        combines = [r for r in combine_rows if r["season"] == str(year)]
        drafts = [r for r in draft_rows if r["season"] == str(year)]
        completed_games = [r for r in game_rows if r["season"] == str(year)
                           and r["home_score"] and r["away_score"]]
        observed_inputs.append({"year": year, "combineRows": len(combines),
                                "draftSelections": len(drafts),
                                "completedGameRows": len(completed_games),
                                "regularSeasonGameRows": sum(r["game_type"] == "REG" for r in completed_games)})
    expected = {2018: {"dataset": "data/processed/scenario-2018.json", "teams": 32,
                       "slots": 256, "playableCombinePool": 336, "actualPicks": 256,
                       "compensatoryFlags": 32, "compensatoryFlagsKnown": True},
                **{r["year"]: {"dataset": r["dataset"], "teams": r["checks"]["initialOwnerFranchises"],
                               "slots": r["checks"]["draftSlots"],
                               "playableCombinePool": r["checks"]["combinePoolRows"],
                               "actualPicks": r["checks"]["actualSelectionsResolved"],
                               "officialOrderMismatchBeforeOverride": r["checks"]["officialOrderMismatchesBeforePrimaryOverride"],
                               "compensatoryFlags": (None if r["year"] in {2019, 2021} else
                                   sum(p.get("compensatory", False) for p in
                                       json.loads((OUT / f"scenario-{r['year']}.json").read_text())["picks"])),
                               "compensatoryFlagsKnown": r["year"] not in {2019, 2021}}
                   for r in report}}
    return {"schemaVersion": 1, "verifiedDate": datetime.now(timezone.utc).date().isoformat(),
            "method": "Fail closed: a year is built only when the pre-draft pool scope and slot ownership are explicitly supportable. Actual draft outcomes remain isolated.",
            "scenarios": years,
            "expectedCoverageByYear": expected,
            "observedRawInputsByYear": observed_inputs,
            "researchAlphaYears": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
            "blockedYears": [],
            "2021InviteeSource": "https://www.giants.com/news/2021-nfl-scouting-combine-list-of-invited-prospects-new-format-nfl-draft",
            "2020To2024OwnershipAudit": "Primary order rows, publication/as-of evidence, and normalized sequence hashes are in data/clean/additional_order_sources.json; source captures are text extracted from official pages, not original HTTP bytes.",
            "2025OwnershipAudit": "Primary NFL.com round-by-round order compared to corrected reversal; primary owner sequence is pinned in research/build_scenarios.py.",
            "2026OwnershipAudit": "NFL Football Operations April 22 order PDF is the primary owner source; 113 trade-reversal differences are overridden and retained in the manifest.",
            "notSupportedAsFullRelease": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    reports = []
    for year in SCENARIO_CUTOFFS:
        dataset, report = build_scenario(year)
        (OUT / f"scenario-{year}.json").write_text(json.dumps(dataset, separators=(",", ":")) + "\n")
        reports.append(report)
    (OUT / "scenario-coverage.json").write_text(json.dumps(coverage_manifest(reports), indent=2) + "\n")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
