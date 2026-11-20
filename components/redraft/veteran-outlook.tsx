'use client';
import projections from '@/analytics/workload_regression/projections.json';

interface TeamProjection {
  teamId: string;
  priorHighUsage: number;
  expectedHighUsageAnywhere: number;
  positions: Partial<Record<string, number[]>>;
}
interface DraftProjection {
  latestRegularSeasonGame: string;
  teams: TeamProjection[];
}
export default function VeteranOutlook({year, team}: {year: number; team: string}) {
  const drafts: Record<string, DraftProjection> = projections.drafts;
  const origin = drafts[year];
  const entry = origin?.teams.find(row => row.teamId === team);
  if (!entry) return null;
  return <section className="veteran-outlook" aria-label="Veteran workload outlook">
    <h3>Who could carry a workload again?</h3>
    <p><strong>{entry.priorHighUsage} veterans</strong> were last recorded with this team in the regular season and logged at least 500 offensive or defensive snaps in {year - 1}. The model expects <strong>{entry.expectedHighUsageAnywhere.toFixed(1)}</strong> of them to reach that mark on any NFL team in {year}.</p>
    <details><summary>Explore last season’s position groups</summary>
      <p>Includes lighter-use players as well. A snap is one play on offense or defense. Expected counts can be fractional.</p>
      <table><caption>Prior contributors and expected players with 500 snaps anywhere in {year}</caption>
        <thead><tr><th scope="col">Position</th><th scope="col">Prior players</th><th scope="col">Expected</th></tr></thead>
        <tbody>{Object.entries(entry.positions).filter((item): item is [string, number[]] => item[1] !== undefined).sort(([a],[b])=>a.localeCompare(b)).map(([pos,row])=>
          <tr key={pos}><th scope="row">{pos}</th><td>{row[0]}</td><td>{row[1].toFixed(1)}</td></tr>)}</tbody>
      </table>
      <p>Exploratory model using position and prior snap history through {origin.latestRegularSeasonGame}. Players may have changed teams since that date. These are league playing-time estimates.</p>
    </details>
  </section>;
}
