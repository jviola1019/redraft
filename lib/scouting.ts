/** Server-only disclosure policy. Never serialize policy.profiles or pooledModels directly. */
import { isPlayableProspect, positionGroup, projectionFor, type RuntimeModels } from './engine';
import type { Dataset, GameState, Prospect } from './types';

export const BLIND_POLICY_VERSION = 'blind-g5-v1';
export const MIN_PROFILE_SIZE = 5;
export const MEASUREMENTS = [
    { field: 'heightIn', display: 'height', width: 3, unit: 'in' },
    { field: 'weightLb', display: 'weight', width: 15, unit: 'lb' },
    { field: 'forty', display: 'forty', width: .2, unit: 's' },
    { field: 'bench', display: 'bench', width: 5, unit: 'reps' },
    { field: 'verticalIn', display: 'vertical', width: 5, unit: 'in' },
    { field: 'broadJumpIn', display: 'broad', width: 10, unit: 'in' },
    { field: 'cone', display: 'cone', width: .2, unit: 's' },
    { field: 'shuttle', display: 'shuttle', width: .2, unit: 's' },
] as const;
export type DisplayMeasurements = Record<typeof MEASUREMENTS[number]['display'], string>;
export interface MaskProfile {
    /** Internal identifiers and membership are not part of the browser DTO. */
    groupKey: string;
    memberIds: string[];
    position: string;
    displayMeasurements: DisplayMeasurements;
    pooledProbability: number;
    supported: boolean;
    fallback: boolean;
    probabilityBand: { lower: number; upper: number; midpoint: number; label: string } | null;
}
export interface ScoutingPolicy {
    profiles: Record<string, MaskProfile>;
    pooledModels: RuntimeModels;
    audit: {
        policyVersion: string; baseModelVersion: string; playableProspects: number;
        groupCount: number; minimumGroupSize: number; maximumGroupSize: number;
        initialJointProfileMinimum: number; claim: string;
    };
}
export interface AliasCatalog { toPublic: Map<string, string>; toCanonical: Map<string, string> }
export function broadPosition(position: string): string {
    const group = positionGroup(position);
    return ['K', 'P', 'LS'].includes(group) ? 'ST' : group;
}
export function probabilityBand(probability: number) {
    const lower = Math.min(.9, Math.max(0, Math.floor((probability + 1e-12) * 10) / 10));
    const upper = Math.min(1, Number((lower + .1).toFixed(1)));
    return { lower, upper, midpoint: Number(((lower + upper) / 2).toFixed(2)), label: `${Math.round(lower * 100)}–${Math.round(upper * 100)}%` };
}
function range(values: number[], width: number, unit: string): string {
    if (!values.length) return 'Withheld';
    const lower = Math.floor((Math.min(...values) + 1e-9) / width) * width;
    const upper = Math.ceil((Math.max(...values) - 1e-9) / width) * width;
    const format = (value: number) => Number(value.toFixed(2)).toString();
    return `${format(lower)}–${format(upper)} ${unit}`;
}
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
/** Uses only prospect features and frozen pre-draft projections, never picks/outcomes. */
export function createScoutingPolicy(dataset: Dataset, models: RuntimeModels): ScoutingPolicy {
    const playable = dataset.prospects.filter(isPlayableProspect);
    if (!playable.length) throw new Error('No historically eligible prospect pool.');
    const byPosition = new Map<string, Prospect[]>();
    const raw = new Map(playable.map(p => [p.id, projectionFor(p, models)]));
    const fallback = models.prospect?.globalPrior ?? .3;
    const value = (p: Prospect) => raw.get(p.id)!.roleProbability ?? fallback;
    for (const p of playable) {
        const position = broadPosition(p.position);
        byPosition.set(position, [...byPosition.get(position) ?? [], p]);
    }
    const profiles: Record<string, MaskProfile> = {};
    const groups: MaskProfile[] = [];
    for (const [position, prospects] of [...byPosition.entries()].sort(([a], [b]) => a.localeCompare(b))) {
        if (prospects.length < MIN_PROFILE_SIZE) throw new Error(`Unsupported blind cohort: ${position} has fewer than ${MIN_PROFILE_SIZE} candidates.`);
        const ordered = [...prospects].sort((a, b) => value(a) - value(b) || a.id.localeCompare(b.id));
        const chunks: Prospect[][] = [];
        for (let i = 0; i < ordered.length; i += MIN_PROFILE_SIZE) chunks.push(ordered.slice(i, i + MIN_PROFILE_SIZE));
        if (chunks.length > 1 && chunks.at(-1)!.length < MIN_PROFILE_SIZE) chunks.at(-2)!.push(...chunks.pop()!);
        chunks.forEach((members, index) => {
            const pooledProbability = members.reduce((sum, p) => sum + value(p), 0) / members.length;
            const displayMeasurements = Object.fromEntries(MEASUREMENTS.map(({ field, display, width, unit }) => [display, range(members.map(p => p[field]).filter(finite), width, unit)])) as DisplayMeasurements;
            const supported = members.every(p => raw.get(p.id)!.supported);
            const profile: MaskProfile = {
                groupKey: `${position}-${index}`, memberIds: members.map(p => p.id), position,
                displayMeasurements, pooledProbability, supported, fallback: !supported,
                probabilityBand: position === 'ST' ? null : probabilityBand(pooledProbability),
            };
            groups.push(profile);
            for (const p of members) profiles[p.id] = profile;
        });
    }
    const baseModelVersion = String(models.version ?? models.modelVersion ?? 'unversioned');
    const pooledModels: RuntimeModels = {
        ...models, version: `${baseModelVersion}+${BLIND_POLICY_VERSION}`,
        modelVersion: `${baseModelVersion}+${BLIND_POLICY_VERSION}`,
        prospect: {
            ...models.prospect,
            projections: [
                ...(models.prospect?.projections ?? []).filter(p => !p.prospectId || !profiles[p.prospectId]),
                ...playable.map(p => ({ prospectId: p.id, roleProbability: profiles[p.id].pooledProbability, supported: profiles[p.id].supported, projectionSource: 'Shared pre-draft profile mean' })),
            ],
        },
    };
    const jointCounts = new Map<string, number>();
    for (const p of playable) {
        const profile = profiles[p.id];
        const key = JSON.stringify([profile.position, profile.displayMeasurements, profile.probabilityBand, profile.supported, profile.fallback]);
        jointCounts.set(key, (jointCounts.get(key) ?? 0) + 1);
    }
    return {
        profiles, pooledModels,
        audit: {
            policyVersion: BLIND_POLICY_VERSION, baseModelVersion, playableProspects: playable.length,
            groupCount: groups.length, minimumGroupSize: Math.min(...groups.map(g => g.memberIds.length)),
            maximumGroupSize: Math.max(...groups.map(g => g.memberIds.length)),
            initialJointProfileMinimum: Math.min(...jointCounts.values()),
            claim: 'At least five candidates share each initial released non-ID profile. This is not a guarantee against recognition, elimination, auxiliary data, or collusion.',
        },
    };
}
/** Salt is persisted privately per run; daily participants share a private challenge salt. */
export async function aliasCatalog(salt: string, dataset: Dataset): Promise<AliasCatalog> {
    if (salt.length < 32) throw new Error('Blind aliases require a private salt of at least 32 characters.');
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey('raw', encoder.encode(salt), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
    const entries = await Promise.all(dataset.prospects.map(async p => {
        const hash = await crypto.subtle.sign('HMAC', key, encoder.encode(`${BLIND_POLICY_VERSION}\u0000${p.id}`));
        const digest = [...new Uint8Array(hash)].map(n => n.toString(16).padStart(2, '0')).join('').slice(0, 32);
        return [p.id, `bp_${digest}`] as const;
    }));
    const toPublic = new Map(entries), toCanonical = new Map(entries.map(([canonical, alias]) => [alias, canonical]));
    if (toPublic.size !== dataset.prospects.length || toCanonical.size !== dataset.prospects.length) throw new Error('Duplicate prospect or blind alias.');
    return { toPublic, toCanonical };
}
const profileNotes = 'Shared ranges for a group of at least five prospects, rounded outward from known measurements. They are not individual measurements. Individual missingness and college are withheld; a range does not establish that this candidate completed the test.';
/** Whitelist, not {...prospect}: canonical IDs and raw feature fingerprints never leave here. */
export function identityRevealed(game: GameState, now: Date = new Date()): boolean {
    if (!['ready', 'simulating', 'complete'].includes(game.status)) return false;
    if (game.mode !== 'daily') return true;
    if (!Number.isFinite(new Date(game.createdAt).getTime()) || !Number.isFinite(now.getTime())) return false;
    return new Date(game.createdAt).toISOString().slice(0, 10) < now.toISOString().slice(0, 10);
}
export function prospectViews(game: GameState, dataset: Dataset, models: RuntimeModels, policy: ScoutingPolicy, aliases: AliasCatalog, now: Date = new Date()) {
    const revealed = identityRevealed(game, now);
    const publicId = (id: string) => { const result = aliases.toPublic.get(id); if (!result) throw new Error('Missing blind alias.'); return result; };
    const labels = new Map<string, string>();
    const groupCounts: Record<string, number> = {};
    for (const p of dataset.prospects.filter(isPlayableProspect).sort((a, b) => publicId(a.id).localeCompare(publicId(b.id)))) {
        const group = broadPosition(p.position);
        groupCounts[group] = (groupCounts[group] ?? 0) + 1;
        labels.set(p.id, `${group}-${String(groupCounts[group]).padStart(3, '0')}`);
    }
    return dataset.prospects.filter(p => revealed || isPlayableProspect(p)).map(p => {
        const mask = policy.profiles[p.id];
        if (!revealed && !mask) throw new Error('Missing blind disclosure profile.');
        const id = publicId(p.id), label = labels.get(p.id) ?? `ARCHIVE-${id.slice(-6).toUpperCase()}`;
        const scouted = mask ? mask.memberIds.some(memberId => game.scouted.includes(memberId)) : game.scouted.includes(p.id);
        const raw = revealed ? projectionFor(p, policy.pooledModels) : null;
        const showProjection = revealed || scouted;
        const band = mask?.probabilityBand;
        const projection = {
            prospectId: id,
            roleProbability: showProjection ? (band?.midpoint ?? raw?.roleProbability ?? null) : null,
            roleProbabilityLabel: showProjection ? (band?.label ?? 'Unavailable for this position') : 'Scout to reveal shared range',
            uncertainty: null,
            modelVersion: policy.pooledModels.version,
            target: 'At least 200 rookie-season offensive or defensive snaps',
            supported: showProjection ? (mask?.supported ?? raw?.supported ?? false) : false,
            fallback: showProjection ? (mask?.fallback ?? raw?.fallback ?? true) : true,
        };
        return {
            id, blindName: label, name: revealed ? p.name : label, identityRevealed: revealed,
            position: revealed ? p.position : mask.position,
            college: revealed ? p.college : 'Hidden until reveal',
            heightIn: revealed ? p.heightIn : null, weightLb: revealed ? p.weightLb : null,
            forty: revealed ? p.forty : null, bench: revealed ? p.bench : null,
            verticalIn: revealed ? p.verticalIn : null, broadJumpIn: revealed ? p.broadJumpIn : null,
            cone: revealed ? p.cone : null, shuttle: revealed ? p.shuttle : null,
            displayMeasurements: revealed ? Object.fromEntries(MEASUREMENTS.map(({ field, display, unit }) => [display, finite(p[field]) ? `${p[field]} ${unit}` : 'Not reported'])) as DisplayMeasurements : mask.displayMeasurements,
            profileNotes: revealed ? 'Historical identity and recorded measurements revealed after the draft. Missing values remain unavailable.' : profileNotes,
            ...(revealed ? { source: p.source, availableBy: p.availableBy } : {}),
            scouted, projection,
        };
    }).sort((a, b) => a.position.localeCompare(b.position) || a.blindName.localeCompare(b.blindName));
}
