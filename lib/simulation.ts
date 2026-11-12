import developmentModel from '../analytics/five_year_strict_2018.json';
import { clamp, normal, positionGroup, probability, random, pickValue, scenarioYear, validateGame } from './engine';
import type { RuntimeModels } from './engine';
import type { Dataset, GameState, TeamSeason, SimGame, SeasonResult, PlayerSeason, Selection, SimWorld, ReplicateResult, SimulationResults, ScoreComponent } from './types';
interface Fixture {
    home: string;
    away: string;
    week: number;
}
const DIVISIONS = ['East', 'North', 'South', 'West'];
const MATCHINGS = [[[0, 1], [2, 3]], [[0, 2], [1, 3]], [[0, 3], [1, 2]]];
function compareTeams(a: TeamSeason, b: TeamSeason, games: SimGame[] = []): number {
    const pct = (t: TeamSeason) => (t.wins + t.ties / 2) / Math.max(1, t.wins + t.losses + t.ties);
    const overall = pct(b) - pct(a);
    if (overall)
        return overall;
    const direct = games.filter(g => g.type === 'REG' && ((g.home === a.team && g.away === b.team) || (g.away === a.team && g.home === b.team)));
    if (direct.length) {
        const wins = (team: string) => direct.filter(g => (g.home === team ? g.homeScore : g.awayScore) > (g.home === team ? g.awayScore : g.homeScore)).length;
        const head = wins(b.team) - wins(a.team);
        if (head)
            return head;
    }
    return (b.pointsFor - b.pointsAgainst) - (a.pointsFor - a.pointsAgainst) || b.pointsFor - a.pointsFor || a.team.localeCompare(b.team);
}
type TiebreakScope = 'division' | 'wildcard';
const teamPct = (t: TeamSeason) => (t.wins + t.ties / 2) / Math.max(1, t.wins + t.losses + t.ties);
const pctFromGames = (games: SimGame[], team: string) => {
    const own = games.filter(g => g.home === team || g.away === team);
    return own.length ? own.reduce((n, g) => n + ((g.homeScore === g.awayScore) ? 0.5 : ((g.home === team) === (g.homeScore > g.awayScore)) ? 1 : 0), 0) / own.length : null;
};
/** NFL criteria through net points. Net touchdowns are unavailable in this score-level
 * engine; ties remaining after net points use a disclosed deterministic team-ID fallback.
 * Each awarded place restarts the procedure for every remaining tied club. */
export function rankTiedTeams(candidates: TeamSeason[], dataset: Dataset, games: SimGame[], scope: TiebreakScope): TeamSeason[] {
    const regular = games.filter(g => g.type === 'REG'), info = new Map(dataset.teams.map(t => [t.id, t]));
    const own = (id: string) => regular.filter(g => g.home === id || g.away === id);
    const opponent = (g: SimGame, id: string) => g.home === id ? g.away : g.home;
    const margin = (g: SimGame, id: string) => g.home === id ? g.homeScore - g.awayScore : g.awayScore - g.homeScore;
    const stats = new Map(dataset.teams.map(t => {
        const rows = own(t.id);
        return [t.id, { played: rows.length, credit: rows.reduce((n, g) => n + (margin(g, t.id) > 0 ? 1 : margin(g, t.id) === 0 ? .5 : 0), 0),
            pf: rows.reduce((n, g) => n + (g.home === t.id ? g.homeScore : g.awayScore), 0), pa: rows.reduce((n, g) => n + (g.home === t.id ? g.awayScore : g.homeScore), 0) }];
    }));
    type Criterion = 'head' | 'division' | 'common' | 'conference' | 'victory' | 'schedule' | 'conferenceRank' | 'leagueRank' | 'commonNet' | 'conferenceNet' | 'net';
    const metrics: Criterion[] = scope === 'division'
        ? ['head', 'division', 'common', 'conference', 'victory', 'schedule', 'conferenceRank', 'leagueRank', 'commonNet', 'net']
        : ['head', 'conference', 'common', 'victory', 'schedule', 'conferenceRank', 'leagueRank', 'conferenceNet', 'net'];
    const metric = (group: TeamSeason[], criterion: Criterion): Map<string, number | null> => {
        const sets = group.map(t => new Set(own(t.team).map(g => opponent(g, t.team))));
        const common = [...sets[0]].filter(id => sets.every(set => set.has(id)));
        return new Map(group.map(t => {
            const rows = own(t.team);
            let applicable = rows;
            if (criterion === 'head') {
                applicable = rows.filter(g => group.some(x => x.team === opponent(g, t.team)));
                if (scope === 'wildcard' && group.length > 2) {
                    const meetsAll = group.every(x => x.team === t.team || applicable.some(g => opponent(g, t.team) === x.team));
                    return [t.team, meetsAll && applicable.every(g => margin(g, t.team) > 0) ? 1 : meetsAll && applicable.every(g => margin(g, t.team) < 0) ? -1 : 0];
                }
            }
            if (criterion === 'division') applicable = rows.filter(g => info.get(opponent(g, t.team))?.division === info.get(t.team)?.division && info.get(opponent(g, t.team))?.conference === info.get(t.team)?.conference);
            if (criterion === 'conference' || criterion === 'conferenceNet') applicable = rows.filter(g => info.get(opponent(g, t.team))?.conference === info.get(t.team)?.conference);
            if (criterion === 'common' || criterion === 'commonNet') {
                applicable = rows.filter(g => common.includes(opponent(g, t.team)));
                if (criterion === 'common' && scope === 'wildcard' && applicable.length < 4) return [t.team, null];
            }
            if (criterion === 'victory' || criterion === 'schedule') {
                const opponents = rows.filter(g => criterion === 'schedule' || margin(g, t.team) > 0).map(g => stats.get(opponent(g, t.team))!);
                const played = opponents.reduce((n, x) => n + x.played, 0);
                return [t.team, played ? opponents.reduce((n, x) => n + x.credit, 0) / played : null];
            }
            if (criterion === 'conferenceRank' || criterion === 'leagueRank') {
                const peers = dataset.teams.filter(x => criterion === 'leagueRank' || x.conference === info.get(t.team)?.conference).map(x => stats.get(x.id)!);
                const current = stats.get(t.team)!;
                return [t.team, -peers.filter(x => x.pf > current.pf).length - peers.filter(x => x.pa < current.pa).length];
            }
            if (criterion.endsWith('Net') || criterion === 'net') return [t.team, applicable.length ? applicable.reduce((n, g) => n + margin(g, t.team), 0) : null];
            return [t.team, pctFromGames(applicable, t.team)];
        }));
    };
    const winner = (group: TeamSeason[]): TeamSeason => {
        if (group.length === 1) return group[0];
        for (const criterion of metrics) {
            const values = metric(group, criterion);
            if (group.some(t => values.get(t.team) == null)) continue;
            const best = Math.max(...group.map(t => values.get(t.team)!));
            const retained = group.filter(t => values.get(t.team) === best);
            if (retained.length < group.length) return winner(retained);
        }
        return [...group].sort((a, b) => a.team.localeCompare(b.team))[0];
    };
    const ranked: TeamSeason[] = [], remaining = [...candidates];
    while (remaining.length) {
        const best = Math.max(...remaining.map(teamPct));
        const selected = winner(remaining.filter(t => teamPct(t) === best));
        ranked.push(selected); remaining.splice(remaining.indexOf(selected), 1);
    }
    return ranked;
}
/** Per-conference playoff field, with division winners ranked before wild cards. */
export function playoffSeeds(year: number, conference: string, dataset: Dataset, teams: TeamSeason[], games: SimGame[]): TeamSeason[] {
    const eligible = teams.filter(t => teamInfo(dataset, t.team)?.conference === conference);
    const divisions = [...new Set(eligible.map(t => teamInfo(dataset, t.team)!.division))];
    const winners = divisions.map(div => rankTiedTeams(eligible.filter(t => teamInfo(dataset, t.team)!.division === div), dataset, games, 'division')[0]);
    const orderedWinners = rankTiedTeams(winners, dataset, games, 'wildcard');
    const remaining = eligible.filter(t => !winners.some(w => w.team === t.team));
    const wild: TeamSeason[] = [];
    const divisionOrder = new Map(divisions.map(div => [div, rankTiedTeams(eligible.filter(t => teamInfo(dataset, t.team)!.division === div), dataset, games, 'division')]));
    for (let slot = 0; slot < (year >= 2020 ? 3 : 2); slot++) {
        const reps = [...new Set(remaining.map(t => teamInfo(dataset, t.team)!.division))].map(div => divisionOrder.get(div)!.find(t => remaining.includes(t))!);
        const selected = rankTiedTeams(reps, dataset, games, 'wildcard')[0];
        wild.push(selected);
        remaining.splice(remaining.findIndex(t => t.team === selected.team), 1);
    }
    return [...orderedWinners, ...wild].map((t, i) => ({ ...t, playoff: true, seed: i + 1 }));
}
export function wildcardMatchups(seeds: TeamSeason[], year: number): [string, string][] {
    if (year >= 2020) return [[seeds[1].team, seeds[6].team], [seeds[2].team, seeds[5].team], [seeds[3].team, seeds[4].team]];
    return [[seeds[2].team, seeds[5].team], [seeds[3].team, seeds[4].team]];
}
/** NFL reseeding: the highest remaining seed hosts the lowest remaining seed (2020 NFL Record & Fact Book, postseason site priorities). */
export function divisionalMatchups(seeds: TeamSeason[], survivors: string[]): [string, string][] {
    const rank = new Map(seeds.map(t => [t.team, t.seed!]));
    const ordered = survivors.slice().sort((a, b) => rank.get(a)! - rank.get(b)!);
    if (ordered.length !== 4) throw new Error('Divisional round requires four teams per conference.');
    return [[ordered[0], ordered[3]], [ordered[1], ordered[2]]];
}
function teamInfo(dataset: Dataset, id: string) { return dataset.teams.find(t => t.id === id); }
/** Complete recorded data check, including the documented 2022 BUF-CIN cancellation. */
export function actualSeasonIsComplete(dataset: Dataset, year: number): boolean {
    const teams = dataset.teams.map(t => t.id), regular = dataset.games.filter(g => g.season === year && g.type === 'REG'), postseason = dataset.games.filter(g => g.season === year && g.type !== 'REG');
    const valid = (g: Dataset['games'][number]) => teams.includes(g.home) && teams.includes(g.away) && g.home !== g.away && Number.isFinite(g.homeScore) && Number.isFinite(g.awayScore) && g.homeScore >= 0 && g.awayScore >= 0;
    const uniqueIds = (rows: Dataset['games']) => new Set(rows.map(g => g.id)).size === rows.length;
    if (!uniqueIds(regular) || !uniqueIds(postseason) || !regular.every(valid) || !postseason.every(valid)) return false;
    const canceled2022 = year === 2022 ? 1 : 0;
    const expectedTeamGames = year >= 2021 ? 17 : 16;
    if (regular.length !== teams.length * expectedTeamGames / 2 - canceled2022) return false;
    if (postseason.length !== (year >= 2020 ? 13 : 11)) return false;
    return teams.every(team => {
        const count = regular.filter(g => g.home === team || g.away === team).length;
        const expected = year === 2022 && ['BUF', 'CIN'].includes(team) ? 16 : expectedTeamGames;
        return count === expected;
    });
}
function initialStandings(dataset: Dataset): TeamSeason[] { return dataset.teams.map(t => ({ team: t.id, wins: t.priorWins, losses: t.priorLosses, ties: t.priorTies, pointsFor: t.priorPointsFor, pointsAgainst: t.priorPointsAgainst, playoff: false, seed: null, conferenceChampion: false, champion: false })); }
/** Future schedules use prior simulated division standings and their tiebreaks.
 * If prior game records are unavailable, record/point-differential ordering is an
 * explicit fallback; the complete recorded starting-season schedule is preserved.
 * NFL tiebreak procedures apply to both playoffs and regular-season scheduling:
 * https://www.nfl.com/standings/tie-breaking-procedures */
export function generateSchedule(year: number, dataset: Dataset, prior: TeamSeason[], priorGames?: SimGame[]): Fixture[] {
    if (!Number.isInteger(year) || year < 2018) throw new Error('No pre-cutoff schedule support for this season.');
    const regularGames = year >= 2021 ? 17 : 16, expectedGames = dataset.teams.length * regularGames / 2;
    const observed = dataset.games.filter(g => g.season === year && g.type === 'REG');
    const observedTeams = new Set(observed.flatMap(g => [g.home, g.away]));
    if (year === scenarioYear(dataset) && observed.length === expectedGames && observedTeams.size === dataset.teams.length &&
        dataset.teams.every(t => observed.filter(g => g.home === t.id || g.away === t.id).length === regularGames))
        return observed.map(g => ({ home: g.home, away: g.away, week: g.week }));
    const groups = new Map<string, string[]>();
    const priorRegular = priorGames?.filter(g => g.season === year - 1 && g.type === 'REG');
    for (const conference of ['AFC', 'NFC'])
        for (const div of DIVISIONS) {
            const teams = dataset.teams.filter(t => t.conference === conference && t.division === div);
            if (teams.length !== 4)
                throw new Error('Schedule requires eight four-team divisions.');
            const standings = teams.map(team => prior.find(t => t.team === team.id));
            if (standings.some(t => !t)) throw new Error('Schedule requires prior standings for every franchise.');
            const ranked = priorRegular?.length
                ? rankTiedTeams(standings as TeamSeason[], dataset, priorRegular, 'division')
                : (standings as TeamSeason[]).sort((a, b) => compareTeams(a, b));
            groups.set(`${conference}-${div}`, ranked.map(t => t.team));
        }
    const fixtures: Fixture[] = [], week = (round: number) => round < 8 ? round + 1 : round + 2;
    const add = (a: string, b: string, round: number, flip = false) => fixtures.push({ home: flip ? b : a, away: flip ? a : b, week: week(round) });
    const robin = [[[0, 3], [1, 2]], [[0, 2], [3, 1]], [[0, 1], [2, 3]]];
    for (const list of groups.values())
        for (let r = 0; r < 6; r++)
            for (const [a, b] of robin[r % 3])
                add(list[a], list[b], r, r >= 3);
    const teamMap = new Map(dataset.teams.map(t => [t.id, t])), pairs = new Map<string, Set<string>>();
    // Only fixed division rotation structure is read here: never future scores or realized standings.
    for (const g of dataset.games.filter(g => g.season === year && g.type === 'REG')) {
        const a = teamMap.get(g.home), b = teamMap.get(g.away);
        if (!a || !b)
            throw new Error('Unknown franchise in schedule.');
        const ak = `${a.conference}-${a.division}`, bk = `${b.conference}-${b.division}`;
        if (ak === bk)
            continue;
        const key = [ak, bk].sort().join('|');
        if (!pairs.has(key))
            pairs.set(key, new Set());
        pairs.get(key)!.add([g.home, g.away].sort().join('|'));
    }
    const intra = new Map<string, string>(), cross = new Map<string, string>();
    for (const [key, value] of pairs)
        if (value.size >= 15) {
            const [a, b] = key.split('|'), map = a.slice(0, 3) === b.slice(0, 3) ? intra : cross;
            map.set(a, b);
            map.set(b, a);
        }
    if (intra.size !== 8) {
        intra.clear();
        for (const c of ['AFC', 'NFC'])
            for (const [a, b] of MATCHINGS[(year - 2017) % 3]) {
                intra.set(`${c}-${DIVISIONS[a]}`, `${c}-${DIVISIONS[b]}`);
                intra.set(`${c}-${DIVISIONS[b]}`, `${c}-${DIVISIONS[a]}`);
            }
    }
    if (cross.size !== 8) {
        cross.clear();
        for (let i = 0; i < 4; i++) {
            const a = `AFC-${DIVISIONS[i]}`, b = `NFC-${DIVISIONS[(i + year) % 4]}`;
            cross.set(a, b);
            cross.set(b, a);
        }
    }
    for (const [map, start] of [[intra, 6], [cross, 10]] as [
        Map<string, string>,
        number
    ][]) {
        for (const [a, b] of map) {
            if (a > b)
                continue;
            const aa = groups.get(a)!, bb = groups.get(b)!;
            for (let r = 0; r < 4; r++)
                for (let i = 0; i < 4; i++)
                    add(aa[i], bb[(i + r) % 4], start + r, (i + r + year) % 2 === 1);
        }
    }
    for (const c of ['AFC', 'NFC']) {
        const remaining = MATCHINGS.filter(m => !m.some(([a, b]) => intra.get(`${c}-${DIVISIONS[a]}`) === `${c}-${DIVISIONS[b]}`));
        for (let r = 0; r < 2; r++)
            for (const [a, b] of remaining[r]) {
                const aa = groups.get(`${c}-${DIVISIONS[a]}`)!, bb = groups.get(`${c}-${DIVISIONS[b]}`)!;
                for (let i = 0; i < 4; i++)
                    add(aa[i], bb[i], 14 + r, (year + r) % 2 === 1);
            }
    }
    if (year >= 2021) {
        for (let i = 0; i < 4; i++) {
            const a = `AFC-${DIVISIONS[i]}`, primary = cross.get(a)!, b = `NFC-${DIVISIONS[(DIVISIONS.indexOf(primary.slice(4)) + 2) % 4]}`, aa = groups.get(a)!, bb = groups.get(b)!;
            for (let j = 0; j < 4; j++)
                add(aa[j], bb[j], 16, year % 2 === 0);
        }
    }
    const expected = year >= 2021 ? 17 : 16;
    for (const t of dataset.teams) {
        const own = fixtures.filter(g => g.home === t.id || g.away === t.id);
        if (own.length !== expected || new Set(own.map(g => g.week)).size !== expected)
            throw new Error('Schedule consistency failed.');
    }
    return fixtures.sort((a, b) => a.week - b.week || a.home.localeCompare(b.home));
}
function strengthModel(dataset: Dataset, models?: RuntimeModels) {
    const m = models?.team, initial: Record<string, number> = {};
    for (const t of dataset.teams)
        initial[t.id] = m?.initialStrength?.[t.id] ?? (t.priorPointsFor - t.priorPointsAgainst) / 16;
    return { initial, home: m?.homeAdvantage ?? 2.1, coefficient: m?.strengthCoefficient ?? 0.4, total: m?.meanTotal ?? 43.5, marginSd: m?.gameMarginSd ?? m?.residualMarginSd ?? 14.3, totalSd: m?.residualTotalSd ?? 14.2, rho: m?.residualCorrelation ?? 0, persistence: m?.persistence ?? 0.4, innovation: m?.seasonShockSd ?? 4.7 };
}
export function scoreGame(home: string, away: string, season: number, week: number, type: SimGame['type'], strength: Record<string, number>, seed: string, model: ReturnType<typeof strengthModel>): SimGame {
    // Venue direction distinguishes reciprocal divisional meetings without consuming a shared stream.
    const key = [home, away].join('-'), z1 = normal(seed, season, key, type, 'margin'), z2 = normal(seed, season, key, type, 'total');
    const margin = (type === 'SB' ? 0 : model.home) + (strength[home] - strength[away]) + z1 * model.marginSd;
    const total = Math.max(6, model.total + (model.rho * z1 + Math.sqrt(1 - model.rho ** 2) * z2) * model.totalSd);
    let hs = Math.max(0, Math.round((total + margin) / 2)), as = Math.max(0, Math.round((total - margin) / 2));
    if (hs === 1)
        hs = 2;
    if (as === 1)
        as = 2;
    if (hs === as && (type !== 'REG' || random(seed, season, key, 'tie-resolution') > 0.12)) {
        if (random(seed, season, key, 'ot-winner') < 1 / (1 + Math.exp(-margin / 8)))
            hs += 3;
        else
            as += 3;
    }
    return { id: `${season}-${type}-${week}-${away}-${home}`, season, week, type, home, away, homeScore: hs, awayScore: as };
}
function cohort(selections: Selection[], dataset: Dataset, year: number, seed: string, models?: RuntimeModels): PlayerSeason[] {
    const age = year - scenarioYear(dataset), n = year >= 2021 ? 17 : 16;
    if (age < 0 || age > 4) throw new Error('Development donor evidence supports only the five seasons after the draft.');
    const players = selections.map(s => {
        const p = dataset.prospects.find(p => p.id === s.prospectId);
        if (!p) throw new Error('Historical baseline prospect is missing.');
        const group = positionGroup(p.position), donorPosition = ['K','P','LS'].includes(group) ? 'ST' : group;
        const available = developmentModel.donors.filter(d => d.position === donorPosition);
        if (!available.length) throw new Error(`No pre-cutoff development evidence for ${donorPosition}.`);
        const established = random(seed, 'five-year-role', p.id) < probability(p, models);
        const matched = donorPosition === 'ST' ? available : available.filter(d => d.rookieRole === established);
        const pool = matched.length ? matched : available;
        // Draw a complete observed trajectory once. Yearly outcomes remain correlated.
        const donor = pool[Math.floor(random(seed, 'five-year-donor', p.id) * pool.length)];
        const snaps = donor.snaps[age], games = Math.min(n, donor.games[age]);
        // Snap opportunity is observed; converting it to team strength remains a scenario assumption.
        const contribution = clamp(snaps / 800, 0, 2.1);
        return {prospectId:p.id,team:s.team,season:year,contribution,games,starts:0,group};
    });
    const capacity: Record<string, number> = { QB: 1, RB: 2, WR: 3, TE: 2, OL: 5, DL: 4, LB: 3, DB: 5, K: 1, P: 1, LS: 1 };
    for (const team of dataset.teams)
        for (const group of new Set(players.map(p => p.group))) {
            const list = players.filter(p => p.team === team.id && p.group === group).sort((a, b) => b.contribution - a.contribution);
            let remainingStarts = (capacity[group] ?? 1) * n;
            list.forEach((p, i) => { p.contribution *= i < (capacity[group] ?? 1) ? 1 : 0.25; p.starts = Math.round(Math.min(remainingStarts, p.games, p.games * clamp(p.contribution / 1.3, 0, 1))); remainingStarts -= p.starts; });
        }
    return players.map(({ group: _, ...p }) => p);
}
function draftImpact(players: PlayerSeason[], dataset: Dataset): Record<string, number> {
    const result: Record<string, number> = {};
    for (const t of dataset.teams)
        result[t.id] = 0;
    for (const p of players) {
        const prospect = dataset.prospects.find(s => s.id === p.prospectId)!, group = positionGroup(prospect.position), weight = group === 'QB' ? 3.2 : ['K', 'P', 'LS'].includes(group) ? 0.2 : 1;
        result[p.team] += p.contribution * weight * 0.35;
    }
    const mean = Object.values(result).reduce((s, n) => s + n, 0) / dataset.teams.length;
    for (const key of Object.keys(result))
        result[key] -= mean;
    return result;
}
function playSeason(year: number, dataset: Dataset, prior: TeamSeason[], priorGames: SimGame[] | undefined, strength: Record<string, number>, players: PlayerSeason[], seed: string, model: ReturnType<typeof strengthModel>, game: GameState): SeasonResult {
    const games: SimGame[] = generateSchedule(year, dataset, prior, priorGames).map(f => scoreGame(f.home, f.away, year, f.week, 'REG', strength, seed, model));
    const teams: TeamSeason[] = dataset.teams.map(t => ({ team: t.id, wins: 0, losses: 0, ties: 0, pointsFor: 0, pointsAgainst: 0, playoff: false, seed: null, conferenceChampion: false, champion: false })), map = new Map(teams.map(t => [t.team, t]));
    for (const g of games) {
        const h = map.get(g.home)!, a = map.get(g.away)!;
        h.pointsFor += g.homeScore;
        h.pointsAgainst += g.awayScore;
        a.pointsFor += g.awayScore;
        a.pointsAgainst += g.homeScore;
        if (g.homeScore > g.awayScore) {
            h.wins++;
            a.losses++;
        }
        else if (g.homeScore < g.awayScore) {
            a.wins++;
            h.losses++;
        }
        else {
            h.ties++;
            a.ties++;
        }
    }
    const champions: string[] = [], postWeek = year >= 2021 ? 19 : 18;
    const playoff = (home: string, away: string, type: SimGame['type'], week: number) => { const g = scoreGame(home, away, year, week, type, strength, seed, model); games.push(g); return g.homeScore > g.awayScore ? home : away; };
    for (const conference of ['AFC', 'NFC']) {
        const ids = new Set(dataset.teams.filter(t => t.conference === conference).map(t => t.id)), eligible = teams.filter(t => ids.has(t.team));
        const seeds = playoffSeeds(year, conference, dataset, eligible, games);
        seeds.forEach(s => { Object.assign(map.get(s.team)!, { playoff: true, seed: s.seed }); });
        const wildcardWinners = wildcardMatchups(seeds, year).map(([home, away]) => playoff(home, away, 'WC', postWeek));
        const firstRoundSurvivors = year >= 2020 ? [seeds[0].team, ...wildcardWinners] : [seeds[0].team, seeds[1].team, ...wildcardWinners];
        const div = divisionalMatchups(seeds, firstRoundSurvivors).map(([home, away]) => playoff(home, away, 'DIV', postWeek + 1)).sort((a, b) => map.get(a)!.seed! - map.get(b)!.seed!);
        const winner = playoff(div[0], div[1], 'CON', postWeek + 2);
        map.get(winner)!.conferenceChampion = true;
        champions.push(winner);
    }
    const champion = playoff(champions[0], champions[1], 'SB', postWeek + 4);
    map.get(champion)!.champion = true;
    const stars = [...players].sort((a, b) => b.contribution - a.contribution), mvp = stars[0];
    return { year, teams: teams.sort((a, b) => compareTeams(a, b, games)), games, players, awards: mvp ? [{ award: 'Draft-class MVP', prospectId: mvp.prospectId, team: mvp.team, label: `Highest simulated contribution in the ${game.year} class`, scope: 'Cohort-only model award; not an NFL-wide MVP forecast' }] : [], champion, starPicks: stars.slice(0, 8).map(p => ({ prospectId: p.prospectId, team: p.team, contribution: p.contribution })), trades: year === game.year ? game.trades : [] };
}
function world(game: GameState, selections: Selection[], dataset: Dataset, models: RuntimeModels | undefined, index: number): SimWorld {
    const seed = `${game.seed}|ensemble|${index}`, model = strengthModel(dataset, models), background = { ...model.initial }, seasons: SeasonResult[] = [];
    let prior = initialStandings(dataset);
    let priorGames: SimGame[] | undefined;
    for (let year = game.year; year <= game.year + 4; year++) {
        const players = cohort(selections, dataset, year, seed, models), impact = draftImpact(players, dataset), strength: Record<string, number> = {};
        // The fitted coefficient multiplies lagged realized point differential exactly once.
        for (const t of dataset.teams)
            strength[t.id] = model.coefficient * background[t.id] + normal(seed, 'background-roster', year, t.id) * model.innovation + impact[t.id];
        const season = playSeason(year, dataset, prior, priorGames, strength, players, seed, model, game);
        seasons.push(season);
        prior = season.teams;
        priorGames = season.games;
        for (const t of season.teams)
            background[t.team] = (t.pointsFor - t.pointsAgainst) / (t.wins + t.losses + t.ties);
    }
    const own = seasons.map(s => s.teams.find(t => t.team === game.team)!);
    return { seasons, totalWins: own.reduce((n, t) => n + t.wins, 0), playoffAppearances: own.filter(t => t.playoff).length, titles: own.filter(t => t.champion).length };
}
export function simulateReplicate(game: GameState, index: number, dataset: Dataset, models?: RuntimeModels): ReplicateResult {
    validateGame(game, dataset);
    if (game.selections.length !== game.picks.length)
        throw new Error('Complete all seven rounds first.');
    if (!Number.isInteger(index) || index < 0 || index > 999)
        throw new Error('Invalid replicate index.');
    if (dataset.actualPicks.length !== dataset.picks.length || new Set(dataset.actualPicks.map(p => p.prospectId)).size !== dataset.actualPicks.length || dataset.actualPicks.some(p => !dataset.teams.some(t => t.id === p.team) || !dataset.prospects.some(x => x.id === p.prospectId)))
        throw new Error('Historical baseline draft failed integrity checks.');
    const actual: Selection[] = dataset.actualPicks.map(p => ({ overall: p.overall, round: p.round, team: p.team, prospectId: p.prospectId }));
    return { index, baseline: world({ ...game, trades: [] }, actual, dataset, models, index), alternate: world(game, game.selections, dataset, models, index) };
}
export function compactReplicate(replicate: ReplicateResult, userTeam: string): ReplicateResult {
    if (replicate.index === 0)
        return replicate;
    const compact = (w: SimWorld): SimWorld => ({ ...w, seasons: w.seasons.map(s => ({ ...s, teams: s.teams.filter(t => t.team === userTeam), games: [], players: [], starPicks: [], awards: [], trades: [] })) });
    return { index: replicate.index, baseline: compact(replicate.baseline), alternate: compact(replicate.alternate) };
}
const quantile = (values: number[], q: number) => { const i = (values.length - 1) * q, lo = Math.floor(i), hi = Math.ceil(i); return values[lo] + (values[hi] - values[lo]) * (i - lo); };
export function timelineState(year: number, now = new Date()): 'recorded' | 'incomplete' | 'future' { if (now < new Date(`${year}-09-01T00:00:00Z`))
    return 'future'; return now >= new Date(`${year + 1}-03-01T00:00:00Z`) ? 'recorded' : 'incomplete'; }
export function summarizeResults(game: GameState, replicates: ReplicateResult[], dataset: Dataset, models?: RuntimeModels): SimulationResults {
    if (!replicates.length)
        throw new Error('No simulation results.');
    if (new Set(replicates.map(r => r.index)).size !== replicates.length)
        throw new Error('Duplicate ensemble replicate.');
    const deltas = replicates.map(r => r.alternate.totalWins - r.baseline.totalWins).sort((a, b) => a - b), mean = deltas.reduce((a, b) => a + b, 0) / deltas.length, variance = deltas.length > 1 ? deltas.reduce((s, n) => s + (n - mean) ** 2, 0) / (deltas.length - 1) : 0;
    const value = (ids: string[]) => ids.reduce((n, id) => { const p = dataset.prospects.find(p => p.id === id); return n + (p ? probability(p, models) : 0); }, 0);
    const own = game.selections.filter(s => s.team === game.team), historical = dataset.actualPicks.filter(s => s.team === game.team), altValue = value(own.map(s => s.prospectId)), baseValue = value(historical.map(s => s.prospectId)), evalScore = clamp(50 + 40 * (altValue - baseValue) / Math.max(1, baseValue), 0, 100);
    const groups = own.map(s => positionGroup(dataset.prospects.find(p => p.id === s.prospectId)!.position)), diversity = new Set(groups).size / Math.max(1, Math.min(own.length, 6)), ownTrades = game.trades.filter(t => t.from === game.team || t.to === game.team);
    let tradeNet = 0;
    for (const t of ownTrades) {
        const direction = t.from === game.team ? 1 : -1;
        tradeNet += direction * (t.receive.reduce((n, p) => n + pickValue(p), 0) - t.give.reduce((n, p) => n + pickValue(p), 0));
    }
    const capital = dataset.picks.filter(p => p.owner === game.team).reduce((s, p) => s + pickValue(p.overall), 0);
    const scoreComponents: ScoreComponent[] = [
        { name: 'Projected class value', score: evalScore, weight: 0.30, explanation: 'Rookie-role probability sum compared with the actual class; this is not a career-value estimate.' },
        { name: 'Draft-class balance', score: clamp(diversity * 100, 0, 100), weight: 0.10, explanation: 'Position diversity proxy; complete historical roster needs are unavailable.' },
        { name: 'Trade capital', score: clamp(50 + 100 * tradeNet / Math.max(100, capital), 0, 100), weight: 0.15, explanation: 'Net change under the published Johnson chart, with a one-point extension after pick224; acceptance is heuristic.' },
        { name: 'Paired five-year difference', score: clamp(50 + mean * 5, 0, 100), weight: 0.35, explanation: 'Mean simulated wins gained against the paired baseline; sensitive to unvalidated development assumptions.' },
        { name: 'Scouting coverage', score: 100 * own.filter(s => game.scouted.includes(s.prospectId)).length / Math.max(1, own.length), weight: 0.10, explanation: 'Share of selections researched; an activity measure, not empirical scouting skill.' }
    ];
    const actual = Array.from({ length: 5 }, (_, i) => {
        const year = game.year + i, calendarState = timelineState(year), teamGames = dataset.games.filter(g => g.season === year && (g.home === game.team || g.away === game.team));
        const regular = teamGames.filter(g => g.type === 'REG');
        const state: SimulationResults['actual'][number]['state'] = calendarState === 'future' ? 'future' : calendarState === 'recorded' && actualSeasonIsComplete(dataset, year) ? 'recorded' : 'incomplete';
        const recorded = state === 'recorded';
        return { year, state, wins: !recorded ? null : regular.filter(g => (g.home === game.team ? g.homeScore : g.awayScore) > (g.home === game.team ? g.awayScore : g.homeScore)).length, losses: !recorded ? null : regular.filter(g => (g.home === game.team ? g.awayScore : g.homeScore) > (g.home === game.team ? g.homeScore : g.awayScore)).length, ties: !recorded ? null : regular.filter(g => g.homeScore === g.awayScore).length, playoff: !recorded ? null : teamGames.some(g => g.type !== 'REG'), champion: !recorded ? null : teamGames.some(g => g.type === 'SB' && (g.home === game.team ? g.homeScore : g.awayScore) > (g.home === game.team ? g.awayScore : g.homeScore)) };
    });
    return { replicates, summary: { mean, median: quantile(deltas, 0.5), lower: quantile(deltas, 0.1), upper: quantile(deltas, 0.9), probabilityImprovement: deltas.filter(n => n > 0).length / deltas.length, standardError: Math.sqrt(variance / deltas.length), samples: deltas.length }, decisionScore: Math.round(scoreComponents.reduce((n, c) => n + c.score * c.weight, 0)), scoreComponents, actual, limitations: [
            'Research alpha: the rookie snap model does not validate five-year player development or causal draft effects.',
            `The playable pool contains ${dataset.prospects.filter(p => p.eligibilitySource === 'combine-participant').length} recorded combine participants. The historical baseline also includes reference-only non-combine selections, so unequal prospect universes limit comparisons. Other eligible prospects and original publication timestamps are not fully reconstructed.`,
            'Future veterans, contracts, coaching, injuries, trades and draft intake are represented only through an aggregate team-strength process. Individual future roster transactions and league-wide MVP awards are not modeled.',
            'Five-year participation trajectories are sampled from the complete pre-cutoff 2013 cohort. That single cohort cannot establish independent historical calibration; conversion from snaps to team-strength points remains an assumption. Ensemble intervals measure simulation randomness, not full model uncertainty.',
            `The ${game.year} season uses the recorded schedule when complete; otherwise a schedule is generated. Later seasons regenerate standings-dependent opponents using prior simulated division tiebreaks. If prior game records are unavailable, the initial generated schedule falls back to record and point differential. Week placement, home assignments and the 17th-opponent rotation are approximations. Tiebreaks implement score-level criteria through net points; unavailable net touchdowns and final tie resolution remain approximations.`,
            'Scores are rounded continuous draws, with one-point scores mapped to two, rather than possession-by-possession football scores. Overtime is simplified; individual football box scores are not generated.',
            'Trade pricing uses the published Johnson chart with a one-point extension after pick224. Trade frequency is checked against a prior-year count benchmark; acceptance, team styles and composite score weights remain heuristic. Future and conditional picks are unsupported.',
            `The historical baseline uses actual final draft allocations; later real trade obligations are not reconstructed. Draft-class MVP is an illustrative award among ${game.year} prospects only. Two-way prospects use their first source-listed role for gameplay; dual-role development is not modeled.`
        ] };
}
