import type { SimulationResults } from '@/lib/types';

export function resultsTimeline(start: number, team: string, results: SimulationResults) {
    function meanWins(year: number, world: 'baseline' | 'alternate') {
        if (!results.replicates.length) return null;
        let total = 0;
        for (const replicate of results.replicates) {
            const season = replicate[world].seasons.find(s => s.year === year);
            const wins = season?.teams.find(t => t.team === team)?.wins;
            if (wins === undefined || !Number.isFinite(wins)) return null;
            total += wins;
        }
        return total / results.replicates.length;
    }

    const labels = { recorded: 'Recorded', incomplete: 'Incomplete', future: 'Projection' } as const;
    return Array.from({ length: 5 }, (_, i) => {
        const year = start + i;
        const history = results.actual.find(season => season.year === year);
        return {
            year,
            status: history ? labels[history.state] : 'Unavailable',
            actual: history?.state === 'recorded' ? history.wins : null,
            baseline: meanWins(year, 'baseline'),
            alternate: meanWins(year, 'alternate')
        };
    });
}
