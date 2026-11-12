export type GameMode = 'historical' | 'daily';
export type GameStatus = 'drafting' | 'ready' | 'simulating' | 'complete';
export interface Team {
    id: string;
    name: string;
    conference: string;
    division: string;
    priorWins: number;
    priorLosses: number;
    priorTies: number;
    priorPointsFor: number;
    priorPointsAgainst: number;
}
export interface PriorUsageContributor {
    playerId: string;
    name: string;
    position: string;
    scrimmageSnaps: number;
    games: number;
}
export interface PriorUsageGroup {
    group: string;
    totalScrimmageSnaps: number | null;
    players200Plus: number | null;
    positiveSnapPlayers: number | null;
    largestPlayerShare: number | null;
    topContributors?: PriorUsageContributor[];
    complete: boolean;
    policySupported: boolean;
    observedSeason?: number;
    observedThrough?: string;
}
export interface PriorSeasonTeamContext {
    teamId: string;
    priorSeason: number;
    observedThrough: string;
    regularGames: number;
    groups: PriorUsageGroup[];
    priorHeadCoaches: { name: string; games: number }[];
    draftDayRoster: null;
    draftDayCoaches: null;
    scheme: null;
    rosterContinuity: null;
}
export interface PriorSeasonContextDataset {
    metadata: Record<string, unknown>;
    teams: PriorSeasonTeamContext[];
}
export interface PriorUsagePolicy {
    version: string;
    sourceVersion: string;
    sourceSha256: string;
    observedSeason: number;
    observedThrough: string;
    informationCutoff: string;
    coefficientCap: number;
    label: string;
    interpretation: string;
    positionAdjustments: Record<string, Record<string, number>>;
    leagueReferences: Record<string, { medianShare: number | null; iqr: number | null; teams: number }>;
}
export interface Prospect {
    id: string;
    name: string;
    position: string;
    college: string;
    heightIn: number | null;
    weightLb: number | null;
    forty: number | null;
    bench: number | null;
    verticalIn: number | null;
    broadJumpIn: number | null;
    cone: number | null;
    shuttle: number | null;
    source: string;
    availableBy: string;
    eligibilitySource?: string;
}
export interface DraftPick {
    overall: number;
    round: number;
    owner: string;
    compensatory?: boolean;
}
export interface HistoricalGame {
    id: string;
    season: number;
    type: string;
    week: number;
    date: string;
    home: string;
    away: string;
    homeScore: number;
    awayScore: number;
}
export interface Dataset {
    metadata: Record<string, unknown>;
    teams: Team[];
    prospects: Prospect[];
    picks: DraftPick[];
    actualPicks: {
        overall: number;
        round: number;
        team: string;
        prospectId: string;
    }[];
    games: HistoricalGame[];
}
export interface Projection {
    prospectId: string;
    roleProbability: number | null;
    uncertainty: number | null;
    modelVersion: string;
    target: string;
    supported: boolean;
    fallback: boolean;
    missingMeasurements: number;
}
export interface Selection {
    overall: number;
    round: number;
    team: string;
    prospectId: string;
}
export interface Trade {
    id: string;
    atPick: number;
    from: string;
    to: string;
    give: number[];
    receive: number[];
    cpu: boolean;
}
export interface TradeOffer {
    target: string;
    give: number[];
    receive: number[];
}
export interface TradeEvaluation {
    accepted: boolean;
    giveValue: number;
    receiveValue: number;
    ratio: number;
    reason: string;
    counter: TradeOffer | null;
}
export interface GameState {
    id: string;
    year: number;
    team: string;
    mode: GameMode;
    seed: string;
    status: GameStatus;
    cutoff: string;
    datasetVersion: string;
    modelVersion: string;
    engineVersion: string;
    scoringVersion: string;
    ensembleSize: number;
    picks: DraftPick[];
    selections: Selection[];
    trades: Trade[];
    scouted: string[];
    scoutingPoints: number;
    board: string[];
    createdAt: string;
    updatedAt: string;
    revision: number;
    results?: SimulationResults;
}
export interface TeamSeason {
    team: string;
    wins: number;
    losses: number;
    ties: number;
    pointsFor: number;
    pointsAgainst: number;
    playoff: boolean;
    seed: number | null;
    conferenceChampion: boolean;
    champion: boolean;
}
export interface SimGame {
    id: string;
    season: number;
    week: number;
    type: 'REG' | 'WC' | 'DIV' | 'CON' | 'SB';
    home: string;
    away: string;
    homeScore: number;
    awayScore: number;
}
export interface PlayerSeason {
    prospectId: string;
    team: string;
    season: number;
    contribution: number;
    games: number;
    starts: number;
}
export interface SimAward {
    award: string;
    prospectId: string | null;
    team: string;
    label: string;
    scope: string;
}
export interface SeasonResult {
    year: number;
    teams: TeamSeason[];
    games: SimGame[];
    players: PlayerSeason[];
    awards: SimAward[];
    champion: string;
    starPicks: {
        prospectId: string;
        team: string;
        contribution: number;
    }[];
    trades: Trade[];
}
export interface SimWorld {
    seasons: SeasonResult[];
    totalWins: number;
    playoffAppearances: number;
    titles: number;
}
export interface ReplicateResult {
    index: number;
    baseline: SimWorld;
    alternate: SimWorld;
}
export interface ComparisonSummary {
    mean: number;
    median: number;
    lower: number;
    upper: number;
    probabilityImprovement: number;
    standardError: number;
    samples: number;
}
export interface ScoreComponent {
    name: string;
    score: number;
    weight: number;
    explanation: string;
}
export interface SimulationResults {
    replicates: ReplicateResult[];
    summary: ComparisonSummary;
    decisionScore: number;
    scoreComponents: ScoreComponent[];
    actual: {
        year: number;
        wins: number | null;
        losses: number | null;
        ties: number | null;
        playoff: boolean | null;
        champion: boolean | null;
        state: 'recorded' | 'incomplete' | 'future';
    }[];
    limitations: string[];
}
