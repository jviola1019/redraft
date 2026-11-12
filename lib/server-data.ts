// Server-only imports. Historical context and prospect disclosures use separate explicit DTOs.
import source from '@/data/processed/scenario-2018.json';
import rawModels from '@/analytics/model.json';
import scoringRecalibration from '@/analytics/scoring_recalibration.json';
import contextSource from '@/data/clean/team_context_2018.json';
import contextManifest from '@/data/clean/team_context_source_manifest.json';
import type { Dataset, PriorSeasonContextDataset, PriorSeasonTeamContext } from './types';
import { createUsagePolicy, validateScoringRecalibration, type RuntimeModels } from './engine';
import { createScoutingPolicy } from './scouting';
export const dataset = source as unknown as Dataset;
const context = contextSource as unknown as PriorSeasonContextDataset;
if (context.teams.some(team => !dataset.teams.some(t => t.id === team.teamId))) throw new Error('Historical context contains an unknown franchise.');
export const usagePolicy = createUsagePolicy(context, String(dataset.metadata.informationCutoff), contextManifest.artifactSha256);
export const scoutingPolicy = createScoutingPolicy(dataset, rawModels as unknown as RuntimeModels);
validateScoringRecalibration(scoringRecalibration, String(dataset.metadata.informationCutoff));
export const models: RuntimeModels = {
    ...scoutingPolicy.pooledModels,
    usagePolicy,
    team: { ...scoutingPolicy.pooledModels.team, meanTotal: scoringRecalibration.proposedOverride.meanTotal },
    version: `${scoutingPolicy.pooledModels.version}+five-year-2013-v1+${usagePolicy.version}:${usagePolicy.sourceSha256.slice(0, 12)}+scoring-trailing3-v1`,
};
export const teamContextMetadata = {
    version: context.metadata.version, artifactSha256: usagePolicy.sourceSha256,
    observedSeason: context.metadata.observedSeason, observedThrough: context.metadata.observedThrough,
    originalAvailability: context.metadata.originalAvailability, availabilityBasis: context.metadata.availabilityBasis,
    sources: context.metadata.sources, limitations: context.metadata.limitations,
    policy: { version: usagePolicy.version, coefficientCap: usagePolicy.coefficientCap, interpretation: usagePolicy.interpretation },
};
function contextView(team: PriorSeasonTeamContext, contributors: boolean) {
    return {
        teamId: team.teamId, priorSeason: team.priorSeason, observedThrough: team.observedThrough, regularGames: team.regularGames,
        groups: team.groups.map(group => ({
            group: group.group, totalScrimmageSnaps: group.totalScrimmageSnaps,
            players200Plus: group.players200Plus, positiveSnapPlayers: group.positiveSnapPlayers,
            largestPlayerShare: group.largestPlayerShare, complete: group.complete, policySupported: group.policySupported,
            ...(contributors ? { topContributors: (group.topContributors ?? []).slice(0, 4).map(p => ({ playerId: p.playerId, name: p.name, position: p.position, scrimmageSnaps: p.scrimmageSnaps, games: p.games })) } : {}),
        })),
        priorHeadCoaches: team.priorHeadCoaches.map(c => ({ name: c.name, games: c.games })),
        draftDayRoster: null, draftDayCoaches: null, scheme: null, rosterContinuity: null,
        usagePolicy: { label: usagePolicy.label, coefficientCap: usagePolicy.coefficientCap, positionAdjustments: usagePolicy.positionAdjustments[team.teamId], interpretation: usagePolicy.interpretation },
    };
}
export const teamContexts = context.teams.map(team => contextView(team, false));
export function selectedTeamContext(teamId: string) {
    const team = context.teams.find(t => t.teamId === teamId);
    return team ? contextView(team, true) : null;
}
