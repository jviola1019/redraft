'use client';

import { useId, useState } from 'react';
import type { GameState, ReplicateResult } from '@/lib/types';
import { playerDevelopment } from './player-development';

type Props = {
  game: GameState;
  runs: ReplicateResult[];
  revealed: boolean;
  playerName: (id: string) => string;
};

const displayCount = (value: number | null) => value ?? '—';

export function PlayerDevelopmentPanel({ game, runs, revealed, playerName }: Props) {
  const headingId = useId();
  const selectId = useId();
  const noteId = useId();
  const [pickNumber, setPickNumber] = useState<number>();
  const development = playerDevelopment(game, runs, revealed);
  const selection = development.find(({ pick }) => pick.overall === pickNumber) ?? development[0];

  return <section className="panel space-bottom" aria-labelledby={headingId}>
    <div className="panel-head"><h2 id={headingId}>Player development</h2></div>
    {!revealed ? <p className="draft-empty">Player development unlocks after the daily challenge closes.</p> :
      selection ? <>
        <div className="panel-body">
          <label htmlFor={selectId} style={{ display: 'block', fontWeight: 700, marginBottom: 6 }}>Draft pick</label>
          <select id={selectId} className="select-control" style={{ maxWidth: '100%', minWidth: 'min(100%, 16rem)' }}
            value={selection.pick.overall} onChange={event => setPickNumber(Number(event.target.value))}>
            {development.map(({ pick }) => <option key={pick.overall} value={pick.overall}>#{pick.overall} · {playerName(pick.prospectId)}</option>)}
          </select>
          <p className="small-copy" id={noteId}>Five regular seasons in one simulated alternate timeline. Start share is the percentage of team games the player started. Contribution is the simulator’s workload-based input to team strength. A dash marks missing data.</p>
        </div>
        <div className="mobile-scroll" tabIndex={0} role="region" aria-label="Player development table">
          <table className="leaderboard" aria-label={`${playerName(selection.pick.prospectId)} development`} aria-describedby={noteId}>
            <thead><tr>
              <th scope="col">Season</th><th scope="col">Games</th><th scope="col">Starts</th><th scope="col">Start share</th><th scope="col">Contribution</th>
            </tr></thead>
            <tbody>{selection.seasons.map(row => <tr key={row.year}>
              <th scope="row"><strong>{row.year}</strong></th>
              <td>{displayCount(row.games)}</td>
              <td>{displayCount(row.starts)}</td>
              <td>{row.startShare === null ? '—' : <>
                <span>{Math.round(row.startShare * 100)}%</span>
                <span className="score-track" style={{ display: 'block', minWidth: '3.5rem' }} aria-hidden="true"><i style={{ width: `${row.startShare * 100}%` }} /></span>
              </>}</td>
              <td>{row.contribution?.toFixed(2) ?? '—'}</td>
            </tr>)}</tbody>
          </table>
        </div>
      </> : <p className="draft-empty">This franchise made no draft picks in the alternate timeline.</p>}
  </section>;
}
