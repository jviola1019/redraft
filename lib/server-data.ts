// Server-only imports. Each dated scenario is paired with its own frozen model
// contract and disclosure policy; actual history is never used as a feature.
import source2018 from '@/data/processed/scenario-2018.json';
import source2019 from '@/data/processed/scenario-2019.json';
import source2020 from '@/data/processed/scenario-2020.json';
import source2021 from '@/data/processed/scenario-2021.json';
import source2022 from '@/data/processed/scenario-2022.json';
import source2023 from '@/data/processed/scenario-2023.json';
import source2024 from '@/data/processed/scenario-2024.json';
import source2025 from '@/data/processed/scenario-2025.json';
import source2026 from '@/data/processed/scenario-2026.json';
import coverageSource from '@/data/processed/scenario-coverage.json';
import rawModels from '@/analytics/model.json';
import model2019Artifact from '@/analytics/model-2019.json';
import model2020Artifact from '@/analytics/model-2020.json';
import model2021Artifact from '@/analytics/model-2021.json';
import model2022Artifact from '@/analytics/model-2022.json';
import model2023Artifact from '@/analytics/model-2023.json';
import model2024Artifact from '@/analytics/model-2024.json';
import model2025Artifact from '@/analytics/model-2025.json';
import model2026Artifact from '@/analytics/model-2026.json';
import scoringRecalibration from '@/analytics/scoring_recalibration.json';
import contextSource from '@/data/clean/team_context_2018.json';
import contextManifest from '@/data/clean/team_context_source_manifest.json';
import type { Dataset, PriorSeasonContextDataset, PriorSeasonTeamContext } from './types';
import { createUsagePolicy, validateScoringRecalibration, type RuntimeModels } from './engine';
import { BLIND_POLICY_VERSION, createScoutingPolicy } from './scouting';

const dataset2018 = source2018 as unknown as Dataset;
const dataset2019 = source2019 as unknown as Dataset;
const dataset2020 = source2020 as unknown as Dataset;
const dataset2021 = source2021 as unknown as Dataset;
const dataset2022 = source2022 as unknown as Dataset;
const dataset2023 = source2023 as unknown as Dataset;
const dataset2024 = source2024 as unknown as Dataset;
const dataset2025 = source2025 as unknown as Dataset;
const dataset2026 = source2026 as unknown as Dataset;
const context2018 = contextSource as unknown as PriorSeasonContextDataset;
const raw = rawModels as unknown as RuntimeModels;
const meanTotal = scoringRecalibration.proposedOverride.meanTotal;
validateScoringRecalibration(scoringRecalibration, String(dataset2018.metadata.informationCutoff));
validateScoringRecalibration(scoringRecalibration, String(dataset2019.metadata.informationCutoff));
validateScoringRecalibration(scoringRecalibration, String(dataset2020.metadata.informationCutoff));
validateScoringRecalibration(scoringRecalibration, String(dataset2021.metadata.informationCutoff));
validateScoringRecalibration(scoringRecalibration, String(dataset2022.metadata.informationCutoff));
validateScoringRecalibration(scoringRecalibration, String(dataset2023.metadata.informationCutoff));
validateScoringRecalibration(scoringRecalibration, String(dataset2024.metadata.informationCutoff));
validateScoringRecalibration(scoringRecalibration, String(dataset2025.metadata.informationCutoff));
validateScoringRecalibration(scoringRecalibration, String(dataset2026.metadata.informationCutoff));

function marginStrengthsFromKnownRegularSeason(dataset: Dataset, season: number): Record<string, number> {
    const teams = dataset.teams.map(team => team.id);
    const margins = new Map(teams.map(team => [team, 0]));
    const gamesByTeam = new Map(teams.map(team => [team, 0]));
    const games = dataset.games.filter(game => game.season === season && game.type === 'REG');
    if (games.length === 0) throw new Error(`Missing known ${season} regular-season games for team strength initialization.`);
    for (const game of games) {
        if (!margins.has(game.home) || !margins.has(game.away)) throw new Error(`Unknown team in ${season} scoring history.`);
        margins.set(game.home, margins.get(game.home)! + game.homeScore - game.awayScore);
        margins.set(game.away, margins.get(game.away)! + game.awayScore - game.homeScore);
        gamesByTeam.set(game.home, gamesByTeam.get(game.home)! + 1);
        gamesByTeam.set(game.away, gamesByTeam.get(game.away)! + 1);
    }
    const expected = season === 2020 ? 16 : season >= 2021 ? 17 : 16;
    for (const team of teams) {
        const teamExpected = season === 2022 && ['BUF', 'CIN'].includes(team) ? 16 : expected;
        if (gamesByTeam.get(team) !== teamExpected) throw new Error(`${season} scoring history has ${gamesByTeam.get(team)} games for ${team}; expected ${teamExpected}.`);
    }
    return Object.fromEntries(teams.map(team => [team, margins.get(team)! / gamesByTeam.get(team)!]));
}

if (context2018.teams.some(team => !dataset2018.teams.some(t => t.id === team.teamId))) throw new Error('Historical context contains an unknown franchise.');
const canonicalTeams = new Map(dataset2018.teams.map(team => [team.id, [team.conference, team.division].join('|')]));
for (const scenario of [dataset2019, dataset2020, dataset2021, dataset2022, dataset2023, dataset2024, dataset2025, dataset2026]) {
    if (scenario.teams.length !== 32 || new Set(scenario.teams.map(team => team.id)).size !== 32 || scenario.teams.some(team => canonicalTeams.get(team.id) !== [team.conference, team.division].join('|')))
        throw new Error(`Scenario ${scenario.metadata.draftYear} team identities do not match the canonical franchise registry.`);
}
const usagePolicy2018 = createUsagePolicy(context2018, String(dataset2018.metadata.informationCutoff), contextManifest.artifactSha256);
const base2018Policy = createScoutingPolicy(dataset2018, raw);
const models2018: RuntimeModels = {
    ...base2018Policy.pooledModels,
    usagePolicy: usagePolicy2018,
    team: { ...base2018Policy.pooledModels.team, meanTotal },
    version: `${base2018Policy.pooledModels.version}+five-year-2013-v1+${usagePolicy2018.version}:${usagePolicy2018.sourceSha256.slice(0, 12)}+scoring-trailing3-v1`,
};
base2018Policy.pooledModels.version = models2018.version;
base2018Policy.pooledModels.modelVersion = models2018.version;
function createScenarioForecastBundle(dataset: Dataset, precedingSeason: number, artifact: {
    version: string; scenarioYear: number; scenarioVersion: string; scenarioInformationCutoff: string;
    fitThroughSeason: number; fitLabelCutoff: string; projections: NonNullable<NonNullable<RuntimeModels['prospect']>['projections']>;
}) {
    const cutoff = Date.parse(String(dataset.metadata.informationCutoff));
    const fitCutoff = Date.parse(artifact.fitLabelCutoff);
    if (artifact.scenarioYear !== dataset.metadata.draftYear || artifact.scenarioVersion !== dataset.metadata.version ||
        artifact.scenarioInformationCutoff !== dataset.metadata.informationCutoff || artifact.fitThroughSeason > 2017 ||
        !Number.isFinite(cutoff) || !Number.isFinite(fitCutoff) || fitCutoff > cutoff ||
        artifact.projections.some(p => !dataset.prospects.some(prospect => prospect.id === p.prospectId)))
        throw new Error(`Frozen model artifact does not match the ${dataset.metadata.draftYear} scenario contract.`);
    const modelBase: RuntimeModels = {
        ...raw,
        version: artifact.version,
        modelVersion: artifact.version,
        usagePolicy: undefined,
        prospect: {
            ...raw.prospect,
            globalPrior: raw.prospect?.globalPrior,
            positionPriors: raw.prospect?.positionPriors,
            target: raw.prospect?.target,
            projections: artifact.projections,
        },
        team: { ...raw.team, initialStrength: marginStrengthsFromKnownRegularSeason(dataset, precedingSeason), meanTotal },
    };
    const scoutingPolicy = createScoutingPolicy(dataset, modelBase);
    const version = `${artifact.version}+${BLIND_POLICY_VERSION}+${String(dataset.metadata.version)}`;
    const models: RuntimeModels = {
        ...scoutingPolicy.pooledModels,
        usagePolicy: undefined,
        version,
        modelVersion: version,
        team: { ...modelBase.team, meanTotal },
    };
    scoutingPolicy.pooledModels.version = version;
    scoutingPolicy.pooledModels.modelVersion = version;
    return { models, scoutingPolicy };
}
const {models: models2019, scoutingPolicy: base2019Policy} = createScenarioForecastBundle(dataset2019, 2018, model2019Artifact as unknown as Parameters<typeof createScenarioForecastBundle>[2]);
const {models: models2020, scoutingPolicy: base2020Policy} = createScenarioForecastBundle(dataset2020, 2019, model2020Artifact as unknown as Parameters<typeof createScenarioForecastBundle>[2]);
const {models: models2021, scoutingPolicy: base2021Policy} = createScenarioForecastBundle(dataset2021, 2020, model2021Artifact as unknown as Parameters<typeof createScenarioForecastBundle>[2]);
const {models: models2022, scoutingPolicy: base2022Policy} = createScenarioForecastBundle(dataset2022, 2021, model2022Artifact as unknown as Parameters<typeof createScenarioForecastBundle>[2]);
const {models: models2023, scoutingPolicy: base2023Policy} = createScenarioForecastBundle(dataset2023, 2022, model2023Artifact as unknown as Parameters<typeof createScenarioForecastBundle>[2]);
const {models: models2024, scoutingPolicy: base2024Policy} = createScenarioForecastBundle(dataset2024, 2023, model2024Artifact as unknown as Parameters<typeof createScenarioForecastBundle>[2]);
const {models: models2025, scoutingPolicy: base2025Policy} = createScenarioForecastBundle(dataset2025, 2024, model2025Artifact as unknown as Parameters<typeof createScenarioForecastBundle>[2]);
const {models: models2026, scoutingPolicy: base2026Policy} = createScenarioForecastBundle(dataset2026, 2025, model2026Artifact as unknown as Parameters<typeof createScenarioForecastBundle>[2]);

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
        usagePolicy: { label: usagePolicy2018.label, coefficientCap: usagePolicy2018.coefficientCap, positionAdjustments: usagePolicy2018.positionAdjustments[team.teamId], interpretation: usagePolicy2018.interpretation },
    };
}
const teamContexts2018 = context2018.teams.map(team => contextView(team, false));
function selectedTeamContext2018(teamId: string) {
    const team = context2018.teams.find(t => t.teamId === teamId);
    return team ? contextView(team, true) : null;
}
const teamContextMetadata2018 = {
    version: context2018.metadata.version, artifactSha256: usagePolicy2018.sourceSha256,
    observedSeason: context2018.metadata.observedSeason, observedThrough: context2018.metadata.observedThrough,
    originalAvailability: context2018.metadata.originalAvailability, availabilityBasis: context2018.metadata.availabilityBasis,
    sources: context2018.metadata.sources, limitations: context2018.metadata.limitations,
    policy: { version: usagePolicy2018.version, coefficientCap: usagePolicy2018.coefficientCap, interpretation: usagePolicy2018.interpretation },
};
const unavailable2019Context = {
    available: false, status: 'not-audited', observedSeason: null, observedThrough: null,
    limitations: ['No dated 2018 draft-day roster or position-use snapshot is wired to the 2019 scenario. The 2017 context is not reused.'],
};
const unavailable2020Context = {
    available: false, status: 'not-audited', observedSeason: null, observedThrough: null,
    limitations: ['No dated 2019 draft-day roster or position-use snapshot is wired to the 2020 scenario. Earlier context is not reused.'],
};
const unavailable2021Context = {
    available: false, status: 'not-audited', observedSeason: null, observedThrough: null,
    limitations: ['No dated 2020 draft-day roster or position-use snapshot is wired to the 2021 scenario. Earlier context is not reused.'],
};
const unavailable2022Context = {
    available: false, status: 'not-audited', observedSeason: null, observedThrough: null,
    limitations: ['No dated 2021 draft-day roster or position-use snapshot is wired to the 2022 scenario. Earlier context is not reused.'],
};
const unavailable2023Context = {
    available: false, status: 'not-audited', observedSeason: null, observedThrough: null,
    limitations: ['No dated 2022 draft-day roster or position-use snapshot is wired to the 2023 scenario. Earlier context is not reused.'],
};
const unavailable2024Context = {
    available: false, status: 'not-audited', observedSeason: null, observedThrough: null,
    limitations: ['No dated 2023 draft-day roster or position-use snapshot is wired to the 2024 scenario. Earlier context is not reused.'],
};
const unavailable2025Context = {
    available: false, status: 'not-audited', observedSeason: null, observedThrough: null,
    limitations: ['No dated 2024 draft-day roster or position-use snapshot is wired to the 2025 scenario. Earlier context is not reused.'],
};
const unavailable2026Context = {
    available: false, status: 'not-audited', observedSeason: null, observedThrough: null,
    limitations: ['No dated 2025 draft-day roster or position-use snapshot is wired to the 2026 scenario. Earlier context is not reused.'],
};

export interface ScenarioBundle {
    year: number;
    dataset: Dataset;
    models: RuntimeModels;
    scoutingPolicy: ReturnType<typeof createScoutingPolicy>;
    teamContexts: unknown[];
    teamContextMetadata: unknown;
    selectedTeamContext: (teamId: string) => unknown;
}
export const scenarioBundles: Record<number, ScenarioBundle> = {
    2018: { year: 2018, dataset: dataset2018, models: models2018, scoutingPolicy: base2018Policy, teamContexts: teamContexts2018, teamContextMetadata: teamContextMetadata2018, selectedTeamContext: selectedTeamContext2018 },
    2019: { year: 2019, dataset: dataset2019, models: models2019, scoutingPolicy: base2019Policy, teamContexts: [], teamContextMetadata: unavailable2019Context, selectedTeamContext: () => null },
    2020: { year: 2020, dataset: dataset2020, models: models2020, scoutingPolicy: base2020Policy, teamContexts: [], teamContextMetadata: unavailable2020Context, selectedTeamContext: () => null },
    2021: { year: 2021, dataset: dataset2021, models: models2021, scoutingPolicy: base2021Policy, teamContexts: [], teamContextMetadata: unavailable2021Context, selectedTeamContext: () => null },
    2022: { year: 2022, dataset: dataset2022, models: models2022, scoutingPolicy: base2022Policy, teamContexts: [], teamContextMetadata: unavailable2022Context, selectedTeamContext: () => null },
    2023: { year: 2023, dataset: dataset2023, models: models2023, scoutingPolicy: base2023Policy, teamContexts: [], teamContextMetadata: unavailable2023Context, selectedTeamContext: () => null },
    2024: { year: 2024, dataset: dataset2024, models: models2024, scoutingPolicy: base2024Policy, teamContexts: [], teamContextMetadata: unavailable2024Context, selectedTeamContext: () => null },
    2025: { year: 2025, dataset: dataset2025, models: models2025, scoutingPolicy: base2025Policy, teamContexts: [], teamContextMetadata: unavailable2025Context, selectedTeamContext: () => null },
    2026: { year: 2026, dataset: dataset2026, models: models2026, scoutingPolicy: base2026Policy, teamContexts: [], teamContextMetadata: unavailable2026Context, selectedTeamContext: () => null },
};
export const years = Object.keys(scenarioBundles).map(Number).sort((a, b) => a - b);
export const coverage = (coverageSource as { scenarios: { year: number; status: string; blockers?: string[]; dataset?: string }[] }).scenarios;
export function getScenario(year: number): ScenarioBundle {
    const bundle = scenarioBundles[year];
    if (!bundle) throw new Error(`Unsupported or unaudited draft year: ${year}`);
    return bundle;
}

// 2018 aliases are retained for modules/tests that intentionally target the
// original scenario. New request handling must use getScenario(game.year).
export const dataset = dataset2018;
export const models = models2018;
export const scoutingPolicy = base2018Policy;
export const usagePolicy = usagePolicy2018;
export const teamContexts = teamContexts2018;
export const teamContextMetadata = teamContextMetadata2018;
export const selectedTeamContext = selectedTeamContext2018;
