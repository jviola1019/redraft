import johnsonChart from '../data/processed/trade-values.json';
import type { Dataset, GameMode, GameState, Prospect, Projection, TradeOffer, TradeEvaluation, PriorSeasonContextDataset, PriorUsagePolicy } from './types';
export interface RuntimeModels {
    version?: string;
    modelVersion?: string;
    tradeArrivalRate?: number;
    usagePolicy?: PriorUsagePolicy;
    prospect?: {
        projections?: {
            prospectId?: string;
            pfrId?: string;
            name?: string;
            roleProbability?: number | null;
            supported?: boolean;
            missingMeasurements?: number;
            projectionSource?: string;
        }[];
        positionPriors?: Record<string, number>;
        globalPrior?: number;
        target?: string;
    };
    team?: {
        homeAdvantage?: number;
        strengthCoefficient?: number;
        meanTotal?: number;
        residualMarginSd?: number;
        residualTotalSd?: number;
        residualCorrelation?: number;
        persistence?: number;
        seasonInnovationSd?: number;
        seasonShockSd?: number;
        gameMarginSd?: number;
        initialStrength?: Record<string, number>;
    };
    [key: string]: unknown;
}
export const RULE_VERSION = 'redraft-research-0.7-multiyear-playoffs';
export const ENSEMBLE_SIZE = 256;
export const SCORING_VERSION = 'research-score-v1';
/** Fail closed on malformed or post-cutoff calibration metadata. */
export function validateScoringRecalibration(artifact: {fitThroughSeason: unknown; cutoff: unknown; proposedOverride: {meanTotal: unknown}}, historicalCutoff: string): void {
    const available = typeof artifact.cutoff === 'string' ? Date.parse(artifact.cutoff) : NaN;
    const cutoff = Date.parse(historicalCutoff);
    const fit = artifact.fitThroughSeason;
    if (!Number.isFinite(available) || !Number.isFinite(cutoff) || available > cutoff ||
        typeof fit !== 'number' || !Number.isInteger(fit) || fit < 1920 || fit >= 2018 ||
        typeof artifact.proposedOverride.meanTotal !== 'number' || !Number.isFinite(artifact.proposedOverride.meanTotal) || artifact.proposedOverride.meanTotal <= 0)
        throw new Error('Scoring recalibration violates the historical cutoff or has invalid parameters.');
}
export const clamp = (n: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, n));
/** Independent keyed streams. Additional scouting/API calls do not consume gameplay randomness. */
export function random(seed: string, ...keys: (string | number)[]): number {
    const value = [seed, ...keys].join('|');
    let h = 2166136261;
    for (let i = 0; i < value.length; i++) {
        h ^= value.charCodeAt(i);
        h = Math.imul(h, 16777619);
    }
    h += 0x6d2b79f5;
    let t = h;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
}
export function normal(seed: string, ...keys: (string | number)[]): number {
    return Math.sqrt(-2 * Math.log(Math.max(1e-12, random(seed, ...keys, 'u')))) * Math.cos(2 * Math.PI * random(seed, ...keys, 'v'));
}
export function positionGroup(pos: string): string {
    const p = pos.toUpperCase();
    // A two-way designation is retained on the prospect. Draft/roster grouping
    // uses its first source-listed role; this is not a two-way development model.
    if (p.includes('/')) return positionGroup(p.split('/')[0]);
    // H-back is a roster role grouped with tight ends; preserve its raw source label.
    if (p === 'H-BACK') return 'TE';
    if (['OT', 'OG', 'C', 'G', 'T', 'OL'].includes(p))
        return 'OL';
    if (['DE', 'DT', 'DL', 'NT'].includes(p))
        return 'DL';
    if (['CB', 'S', 'SAF', 'FS', 'SS', 'DB'].includes(p))
        return 'DB';
    if (['ILB', 'OLB', 'LB', 'EDGE'].includes(p))
        return 'LB';
    if (['RB', 'FB'].includes(p))
        return 'RB';
    return p;
}
/** Canonical IDs prevent the two Jordan Thomas prospects from being conflated. */
export function projectionFor(prospect: Prospect, models?: RuntimeModels): Projection {
    const model = models?.prospect;
    const matches = model?.projections?.filter(p => p.prospectId === prospect.id) ?? [];
    const entry = matches.length === 1 ? matches[0] : undefined;
    const role = entry?.roleProbability;
    const supported = entry?.supported === true && typeof role === 'number' && Number.isFinite(role);
    const specialist = ['K', 'P', 'LS'].includes(positionGroup(prospect.position));
    const prior = model?.positionPriors?.[positionGroup(prospect.position)] ?? model?.globalPrior;
    const value = typeof role === 'number' && Number.isFinite(role) ? role : typeof prior === 'number' && Number.isFinite(prior) ? prior : null;
    return { prospectId: prospect.id, roleProbability: specialist ? null : value === null ? null : clamp(value, 0.005, 0.995), uncertainty: null, modelVersion: models?.version ?? RULE_VERSION, target: 'At least 200 rookie-season offensive or defensive snaps', supported: !specialist && supported, fallback: !supported, missingMeasurements: entry?.missingMeasurements ?? 8 };
}
/** Unsupported specialist probabilities use a disclosed gameplay prior internally, never a model claim. */
export function probability(prospect: Prospect, models?: RuntimeModels): number {
    return projectionFor(prospect, models).roleProbability ?? models?.prospect?.globalPrior ?? 0.3;
}
/** Non-combine prospects identified retrospectively are historical-baseline-only. */
export function isPlayableProspect(prospect: Prospect): boolean { return prospect.eligibilitySource === 'combine-participant'; }
export function createGame(config: {
    id?: string;
    team?: string;
    year?: number;
    seed?: string;
    mode?: GameMode;
    now?: string;
    modelVersion?: string;
}, dataset: Dataset): GameState {
    const year = scenarioYear(dataset);
    if (config.year !== undefined && config.year !== year)
        throw new Error('Configured draft year does not match the dataset.');
    const seed = String(config.seed || `redraft-${year}`);
    const team = config.team || dataset.teams[Math.floor(random(seed, 'assigned-team') * dataset.teams.length)]?.id;
    if (!dataset.teams.some(t => t.id === team))
        throw new Error('Unknown franchise.');
    if (dataset.prospects.filter(isPlayableProspect).length < dataset.picks.length)
        throw new Error('Playable prospect pool is too small for a complete draft.');
    const now = config.now ?? new Date().toISOString();
    const state: GameState = { id: config.id ?? `run-${Math.floor(random(seed, now, team) * 1e12).toString(36)}`, year, team, mode: config.mode ?? 'historical', seed, status: 'drafting', cutoff: String(dataset.metadata.informationCutoff), datasetVersion: String(dataset.metadata.version ?? `dataset-${year}`), modelVersion: config.modelVersion ?? RULE_VERSION, engineVersion: RULE_VERSION, scoringVersion: SCORING_VERSION, ensembleSize: ENSEMBLE_SIZE, picks: dataset.picks.map(p => ({ ...p })).sort((a, b) => a.overall - b.overall), selections: [], trades: [], scouted: [], scoutingPoints: 12, board: [], createdAt: now, updatedAt: now, revision: 0 };
    validateGame(state, dataset);
    return state;
}
/** Resolve the scenario's draft class from its dataset contract; 2013-era donors only support 2018 onward. */
export function scenarioYear(dataset: Dataset): number {
    const metadata = dataset.metadata as Record<string, unknown>;
    const year = metadata.year ?? metadata.draftYear;
    if (typeof year !== 'number' || !Number.isInteger(year) || year < 2018 || year > 9998 ||
        (metadata.year !== undefined && metadata.draftYear !== undefined && metadata.year !== metadata.draftYear))
        throw new Error('Dataset has an unsupported draft year.');
    const cutoff = typeof metadata.informationCutoff === 'string' ? Date.parse(metadata.informationCutoff) : NaN;
    if (!Number.isFinite(cutoff)) throw new Error('Dataset has an invalid information cutoff.');
    return year;
}
export function currentPick(game: GameState) { return game.picks[game.selections.length] ?? null; }
function nextState(game: GameState): GameState { return { ...game, revision: game.revision + 1, picks: game.picks.map(p => ({ ...p })), selections: [...game.selections], trades: [...game.trades], scouted: [...game.scouted], board: [...game.board] }; }
export function validateGame(game: GameState, dataset: Dataset): true {
    const year = scenarioYear(dataset);
    const teams = new Set(dataset.teams.map(t => t.id)), players = new Map(dataset.prospects.map(p => [p.id, p]));
    const cutoff = new Date(game.cutoff).getTime();
    if (game.year !== year || !Number.isFinite(cutoff) || game.cutoff !== String(dataset.metadata.informationCutoff))
        throw new Error('Invalid historical cutoff.');
    const permitted = (id: string) => { const p = players.get(id), available = p ? new Date(p.availableBy).getTime() : NaN; return !!p && isPlayableProspect(p) && Number.isFinite(available) && available <= cutoff; };
    if (game.picks.length !== dataset.picks.length)
        throw new Error('Draft inventory changed.');
    if (new Set(game.picks.map(p => p.overall)).size !== game.picks.length)
        throw new Error('Duplicate pick.');
    if (game.picks.some((p, i) => !teams.has(p.owner) || p.overall !== dataset.picks[i]?.overall || p.round !== dataset.picks[i]?.round))
        throw new Error('Invalid pick identity or owner.');
    if (new Set(game.selections.map(s => s.prospectId)).size !== game.selections.length)
        throw new Error('Prospect selected twice.');
    if (game.selections.length > game.picks.length)
        throw new Error('Too many selections.');
    for (let i = 0; i < game.selections.length; i++) {
        const s = game.selections[i], p = game.picks[i];
        if (s.overall !== p.overall || s.round !== p.round || s.team !== p.owner || !permitted(s.prospectId))
            throw new Error('Selection has invalid ownership or prospect eligibility.');
    }
    if (game.scoutingPoints < 0 || game.scoutingPoints + game.scouted.length !== 12 || new Set(game.scouted).size !== game.scouted.length || game.scouted.some(id => !permitted(id)))
        throw new Error('Invalid scouting budget.');
    if (game.board.length > 100 || new Set(game.board).size !== game.board.length || game.board.some(id => !permitted(id)))
        throw new Error('Invalid draft board.');
    const finished = game.selections.length === game.picks.length;
    if (!['drafting', 'ready', 'simulating', 'complete'].includes(game.status) || (finished && game.status === 'drafting') || (!finished && game.status !== 'drafting'))
        throw new Error('Draft status contradicts completed selections.');
    const owners = new Map(dataset.picks.map(p => [p.overall, p.owner])), ids = new Set<string>();
    for (const t of game.trades) {
        if (ids.has(t.id) || t.from === t.to || !teams.has(t.from) || !teams.has(t.to) || !t.give.length || !t.receive.length || new Set([...t.give, ...t.receive]).size !== t.give.length + t.receive.length)
            throw new Error('Invalid trade record.');
        ids.add(t.id);
        for (const n of t.give) {
            if (n < t.atPick || owners.get(n) !== t.from)
                throw new Error('Trade violates ownership.');
            owners.set(n, t.to);
        }
        for (const n of t.receive) {
            if (n < t.atPick || owners.get(n) !== t.to)
                throw new Error('Trade violates ownership.');
            owners.set(n, t.from);
        }
    }
    if (game.picks.some(p => owners.get(p.overall) !== p.owner))
        throw new Error('Pick ownership does not reconcile to ledger.');
    return true;
}
export function scout(game: GameState, prospectId: string, dataset: Dataset): GameState {
    if (game.status !== 'drafting')
        throw new Error('Scouting closes after the draft.');
    if (!dataset.prospects.some(p => p.id === prospectId && isPlayableProspect(p)))
        throw new Error('Prospect is outside the playable combine-participant pool.');
    if (game.scouted.includes(prospectId))
        return game;
    if (game.scoutingPoints < 1)
        throw new Error('No scouting credits remain.');
    const next = nextState(game);
    next.scouted.push(prospectId);
    next.scoutingPoints--;
    validateGame(next, dataset);
    return next;
}
export function setBoard(game: GameState, ids: string[], dataset: Dataset): GameState {
    if (game.status !== 'drafting')
        throw new Error('The draft board is closed.');
    if (ids.length > 100 || new Set(ids).size !== ids.length || ids.some(id => !dataset.prospects.some(p => p.id === id && isPlayableProspect(p))))
        throw new Error('Invalid board.');
    const next = nextState(game);
    next.board = [...ids];
    return next;
}
function selectForTeam(game: GameState, prospectId: string, dataset: Dataset): GameState {
    if (game.status !== 'drafting')
        throw new Error('Draft is not active.');
    const pick = currentPick(game);
    if (!pick)
        throw new Error('Draft is complete.');
    const p = dataset.prospects.find(p => p.id === prospectId);
    if (!p)
        throw new Error('Unknown prospect.');
    if (!isPlayableProspect(p))
        throw new Error('Prospect is outside the playable combine-participant pool.');
    if (game.selections.some(s => s.prospectId === prospectId))
        throw new Error('Prospect already selected.');
    const available = new Date(p.availableBy).getTime(), cutoff = new Date(game.cutoff).getTime();
    if (!Number.isFinite(available) || !Number.isFinite(cutoff) || available > cutoff)
        throw new Error('Prospect data violates historical cutoff.');
    const next = nextState(game);
    next.selections.push({ overall: pick.overall, round: pick.round, team: pick.owner, prospectId });
    if (next.selections.length === next.picks.length)
        next.status = 'ready';
    return next;
}
export function select(game: GameState, prospectId: string, dataset: Dataset): GameState {
    if (currentPick(game)?.owner !== game.team)
        throw new Error('It is not your selection.');
    const next = selectForTeam(game, prospectId, dataset);
    validateGame(next, dataset);
    return next;
}
export const PRIOR_USAGE_POLICY_VERSION = 'prior-utilization-policy-v1';
export const PRIOR_USAGE_CAP = 0.035;
const USAGE_UNITS = [['QB', 'RB', 'WR', 'TE', 'OL'], ['DL', 'LB', 'DB']];
/** Historical utilization is evidence; its small utility weight is an explicit strategy assumption. */
export function createUsagePolicy(context: PriorSeasonContextDataset, cutoff: string, sourceSha256: string): PriorUsagePolicy {
    const cutoffTime = Date.parse(cutoff);
    const verifyDate = (value: unknown) => {
        const time = typeof value === 'string' ? Date.parse(value) : NaN;
        if (!Number.isFinite(time) || time > cutoffTime) throw new Error('Prior usage context violates the information cutoff.');
    };
    if (!Number.isFinite(cutoffTime) || context.metadata.observedSeason !== 2017 || context.metadata.scenarioYear !== 2018) throw new Error('Unsupported prior usage season.');
    if (!/^[a-f0-9]{64}$/.test(sourceSha256)) throw new Error('Prior usage requires a pinned SHA256 artifact.');
    verifyDate(context.metadata.observedThrough);
    if (context.teams.length !== 32 || new Set(context.teams.map(t => t.teamId)).size !== 32) throw new Error('Prior usage requires 32 unique franchises.');
    const shares: Record<string, Record<string, number | null>> = {};
    for (const team of context.teams) {
        if (team.priorSeason !== 2017) throw new Error('Prior usage contains a later season.');
        verifyDate(team.observedThrough);
        if (new Set(team.groups.map(g => g.group)).size !== team.groups.length) throw new Error('Duplicate prior usage group.');
        for (const group of team.groups) {
            if (group.observedSeason !== undefined && group.observedSeason !== 2017) throw new Error('Prior usage group contains a later season.');
            if (group.observedThrough !== undefined) verifyDate(group.observedThrough);
        }
        shares[team.teamId] = {};
        for (const unit of USAGE_UNITS) {
            const rows = unit.map(group => team.groups.find(g => g.group === group));
            const complete = team.regularGames === 16 && rows.every(g => !!g && g.complete && g.policySupported && typeof g.totalScrimmageSnaps === 'number' && Number.isFinite(g.totalScrimmageSnaps) && g.totalScrimmageSnaps >= 0);
            const total = complete ? rows.reduce((sum, g) => sum + g!.totalScrimmageSnaps!, 0) : 0;
            rows.forEach((g, index) => shares[team.teamId][unit[index]] = complete && total > 0 ? g!.totalScrimmageSnaps! / total : null);
        }
    }
    const quantile = (values: number[], q: number) => {
        const at = (values.length - 1) * q, lo = Math.floor(at), hi = Math.ceil(at);
        return values[lo] + (values[hi] - values[lo]) * (at - lo);
    };
    const positionAdjustments: PriorUsagePolicy['positionAdjustments'] = Object.fromEntries(context.teams.map(t => [t.teamId, {}]));
    const leagueReferences: PriorUsagePolicy['leagueReferences'] = {};
    for (const group of USAGE_UNITS.flat()) {
        const values = context.teams.map(t => shares[t.teamId][group]).filter((v): v is number => typeof v === 'number').sort((a, b) => a - b);
        const median = values.length === 32 ? quantile(values, 0.5) : null;
        const iqr = values.length === 32 ? quantile(values, 0.75) - quantile(values, 0.25) : null;
        leagueReferences[group] = { medianShare: median, iqr, teams: values.length };
        for (const team of context.teams) {
            const share = shares[team.teamId][group];
            positionAdjustments[team.teamId][group] = share !== null && median !== null && iqr !== null && iqr > 1e-12 ? PRIOR_USAGE_CAP * clamp((share - median) / (2 * iqr), -1, 1) : 0;
        }
    }
    return {
        version: PRIOR_USAGE_POLICY_VERSION, sourceVersion: String(context.metadata.version), sourceSha256,
        observedSeason: 2017, observedThrough: String(context.metadata.observedThrough), informationCutoff: cutoff,
        coefficientCap: PRIOR_USAGE_CAP, positionAdjustments, leagueReferences,
        label: 'Prior-use policy adjustment',
        interpretation: 'Capped additive utility from 2017 positional player-snap share within offense or defense. This heuristic reflects prior utilization, not an April 2018 vacancy, roster continuity, player quality, probability, or verified scheme. Incomplete coverage and zero league spread give no adjustment.',
    };
}
export function priorUsageAdjustment(game: GameState, prospect: Prospect, team: string, models?: RuntimeModels): number {
    const policy = models?.usagePolicy;
    if (!policy) return 0;
    if (policy.observedSeason >= game.year || !Number.isFinite(Date.parse(game.cutoff)) || !Number.isFinite(Date.parse(policy.informationCutoff)) || !Number.isFinite(Date.parse(policy.observedThrough)) || Date.parse(policy.observedThrough) > Date.parse(game.cutoff) || Date.parse(policy.informationCutoff) > Date.parse(game.cutoff)) throw new Error('Prior usage policy exceeds the historical cutoff.');
    const adjustment = policy.positionAdjustments[team]?.[positionGroup(prospect.position)];
    return typeof adjustment === 'number' && Number.isFinite(adjustment) ? clamp(adjustment, -PRIOR_USAGE_CAP, PRIOR_USAGE_CAP) : 0;
}
/** Standard competition ranks: 90,90,80 becomes 1,1,3; time only orders tied rows. */
export function rankLeaderboard<T extends { score: number }>(rows: T[]): (T & { rank: number })[] {
    const ordered = [...rows].sort((a, b) => b.score - a.score);
    let rank = 0;
    return ordered.map((row, index) => {
        if (!Number.isFinite(row.score)) throw new Error('Invalid leaderboard score.');
        if (index === 0 || row.score !== ordered[index - 1].score) rank = index + 1;
        return { ...row, rank };
    });
}
function utilityFromCount(game: GameState, prospect: Prospect, team: string, count: number, models?: RuntimeModels): number {
    const group = positionGroup(prospect.position), limits: Record<string, number> = { QB: 1, RB: 1, WR: 2, TE: 1, OL: 3, DL: 2, LB: 2, DB: 3, K: 0.3, P: 0.3, LS: 0.1 };
    const balance = 0.16 * (1 - Math.min(3, count / (limits[group] ?? 1)));
    const premium = group === 'QB' ? 0.08 : ['OL', 'DL', 'DB', 'WR'].includes(group) ? 0.025 : ['K', 'P', 'LS'].includes(group) ? -0.22 : 0;
    return probability(prospect, models) + balance + premium + (random(game.seed, 'cpu-style', team, group) - 0.5) * 0.12 + priorUsageAdjustment(game, prospect, team, models);
}
export function draftUtility(game: GameState, prospect: Prospect, team: string, dataset: Dataset, models?: RuntimeModels): number {
    const group = positionGroup(prospect.position), count = game.selections.filter(s => s.team === team && positionGroup(dataset.prospects.find(p => p.id === s.prospectId)!.position) === group).length;
    return utilityFromCount(game, prospect, team, count, models);
}
function cpuPick(game: GameState, dataset: Dataset, models?: RuntimeModels): string {
    const p = currentPick(game)!, selected = new Set(game.selections.map(s => s.prospectId)), counts: Record<string, number> = {};
    for (const s of game.selections.filter(s => s.team === p.owner)) {
        const group = positionGroup(dataset.prospects.find(x => x.id === s.prospectId)!.position);
        counts[group] = (counts[group] ?? 0) + 1;
    }
    let best: string | null = null, bestU = -Infinity;
    for (const prospect of dataset.prospects) {
        if (!isPlayableProspect(prospect) || selected.has(prospect.id))
            continue;
        const noise = -Math.log(-Math.log(clamp(random(game.seed, 'cpu-choice', p.overall, p.owner, prospect.id), 1e-9, 1 - 1e-9))) * 0.045;
        const value = utilityFromCount(game, prospect, p.owner, counts[positionGroup(prospect.position)] ?? 0, models) + noise;
        if (value > bestU) {
            bestU = value;
            best = prospect.id;
        }
    }
    if (!best)
        throw new Error('Eligible prospect pool exhausted.');
    return best;
}
/** Johnson chart (2014 source); picks beyond 224 use an explicit one-point
 * gameplay extension. This is not an empirically fitted late-pick price. */
export function pickValue(overall: number): number {
    if (!Number.isInteger(overall) || overall < 1 || overall > 400)
        throw new Error('Invalid pick.');
    const row = johnsonChart.values.find(p => p.pick === overall);
    if (!row && overall > 224) return 1;
    if (!row)
        throw new Error('Unpriced selection.');
    return row.gameValue;
}
function validateOffer(game: GameState, offer: TradeOffer, from = game.team): void {
    if (game.status !== 'drafting' || !currentPick(game))
        throw new Error('Trading is closed.');
    if (offer.target === from || !game.picks.some(p => p.owner === offer.target))
        throw new Error('Invalid trade partner.');
    if (!offer.give.length || !offer.receive.length || offer.give.length > 8 || offer.receive.length > 8)
        throw new Error('A trade needs 1–8 selections on each side.');
    if (new Set([...offer.give, ...offer.receive]).size !== offer.give.length + offer.receive.length)
        throw new Error('Duplicate trade asset.');
    const selected = new Set(game.selections.map(s => s.overall));
    for (const n of offer.give)
        if (selected.has(n) || game.picks.find(p => p.overall === n)?.owner !== from)
            throw new Error('You do not own an available offered pick.');
    for (const n of offer.receive)
        if (selected.has(n) || game.picks.find(p => p.overall === n)?.owner !== offer.target)
            throw new Error('Partner does not own an available requested pick.');
}
export function proposeTrade(game: GameState, offer: TradeOffer, dataset: Dataset): TradeEvaluation {
    validateOffer(game, offer);
    if (!dataset.teams.some(t => t.id === offer.target))
        throw new Error('Unknown franchise.');
    const giveValue = offer.give.reduce((s, n) => s + pickValue(n), 0), receiveValue = offer.receive.reduce((s, n) => s + pickValue(n), 0), threshold = 1.04 + random(game.seed, 'trade-policy', offer.target, currentPick(game)!.overall) * 0.1, ratio = giveValue / receiveValue, accepted = ratio >= threshold;
    let counter: TradeOffer | null = null;
    if (!accepted) {
        const extra = game.picks.filter(p => p.owner === game.team && p.overall >= currentPick(game)!.overall && !offer.give.includes(p.overall)).sort((a, b) => b.overall - a.overall);
        let value = giveValue;
        const give = [...offer.give];
        for (const p of extra) {
            if (give.length >= 8)
                break;
            give.push(p.overall);
            value += pickValue(p.overall);
            if (value / receiveValue >= threshold) {
                counter = { target: offer.target, give, receive: [...offer.receive] };
                break;
            }
        }
    }
    return { accepted, giveValue, receiveValue, ratio, reason: accepted ? 'Accepted: the offer clears this team’s value premium.' : counter ? 'Declined. The team requests additional draft capital.' : 'Declined: insufficient available compensation.', counter };
}
function transfer(game: GameState, offer: TradeOffer, from: string, cpu: boolean): GameState {
    validateOffer(game, offer, from);
    const next = nextState(game), atPick = currentPick(game)!.overall;
    for (const p of next.picks) {
        if (offer.give.includes(p.overall))
            p.owner = offer.target;
        else if (offer.receive.includes(p.overall))
            p.owner = from;
    }
    next.trades.push({ id: `trade-${game.trades.length + 1}-${atPick}`, atPick, from, to: offer.target, give: [...offer.give], receive: [...offer.receive], cpu });
    return next;
}
export function applyTrade(game: GameState, offer: TradeOffer, dataset: Dataset): GameState {
    if (!proposeTrade(game, offer, dataset).accepted)
        throw new Error('The trade partner has not accepted these terms.');
    const next = transfer(game, offer, game.team, false);
    validateGame(next, dataset);
    return next;
}
function maybeCpuTrade(game: GameState, dataset: Dataset, models?: RuntimeModels): GameState {
    const on = currentPick(game)!;
    if (on.owner === game.team || random(game.seed, 'trade-arrival', on.overall) > (models?.tradeArrivalRate ?? 0.10))
        return game;
    const teams = dataset.teams.filter(t => t.id !== game.team && t.id !== on.owner).sort((a, b) => random(game.seed, 'buyer', on.overall, a.id) - random(game.seed, 'buyer', on.overall, b.id));
    for (const team of teams) {
        const picks = game.picks.filter(p => p.owner === team.id && p.overall > on.overall).slice(0, 4);
        if (picks.length < 2)
            continue;
        const give: number[] = [];
        let value = 0;
        for (const p of picks) {
            give.push(p.overall);
            value += pickValue(p.overall);
            if (value > pickValue(on.overall) * 1.1) {
                if (value > pickValue(on.overall) * 1.8)
                    break;
                return transfer(game, { target: on.owner, give, receive: [on.overall] }, team.id, true);
            }
        }
    }
    return game;
}
export function advance(game: GameState, dataset: Dataset, models?: RuntimeModels, mode: 'user' | 'one' = 'user'): GameState {
    let next = game, steps = 0;
    while (next.status === 'drafting' && currentPick(next)?.owner !== next.team) {
        next = maybeCpuTrade(next, dataset, models);
        next = selectForTeam(next, cpuPick(next, dataset, models), dataset);
        steps++;
        if (mode === 'one' || steps > dataset.picks.length)
            break;
    }
    validateGame(next, dataset);
    return next;
}
export function autoComplete(game: GameState, dataset: Dataset, models?: RuntimeModels): GameState {
    let next = game;
    while (next.status === 'drafting') {
        if (currentPick(next)?.owner === next.team) {
            const available = next.board.find(id => !next.selections.some(s => s.prospectId === id));
            next = selectForTeam(next, available ?? cpuPick(next, dataset, models), dataset);
        }
        else
            next = advance(next, dataset, models);
    }
    validateGame(next, dataset);
    return next;
}
