'use client';

import { useState } from 'react';
import { ArrowRight, Bookmark, Check, Eye, Shuffle } from 'lucide-react';
import { measurement, positionHelp, roleLabel, type ProspectView } from './types';

export const positionNames: Record<string, string> = {
  QB: 'Quarterback', RB: 'Running back', WR: 'Wide receiver', TE: 'Tight end',
  OL: 'Offensive line', DL: 'Defensive line', LB: 'Linebacker',
  DB: 'Defensive back', ST: 'Special teams',
};

type Props = {
  prospects: ProspectView[];
  board: string[];
  compareIds: string[];
  busy: boolean;
  scoutingPoints: number;
  myTurn: boolean;
  onDetail: (id: string) => void;
  onScout: (id: string) => void;
  onCompare: (id: string) => void;
  draftCounts: { position: string; count: number }[];
};

export default function GuidedBoard({
  prospects, board, compareIds, busy, scoutingPoints, myTurn,
  onDetail, onScout, onCompare, draftCounts,
}: Props) {
  const [startId, setStartId] = useState<string>();
  const [count, setCount] = useState(3);
  const offset = Math.max(0, prospects.findIndex(prospect => prospect.id === startId));
  const ordered = [...prospects.slice(offset), ...prospects.slice(0, offset)];
  const firstByPosition = new Map<string, ProspectView>();
  for (const prospect of ordered) {
    if (!firstByPosition.has(prospect.position)) firstByPosition.set(prospect.position, prospect);
  }
  const unique = [...firstByPosition.values()];
  const featured = [...new Set([...unique, ...ordered])].slice(0, count);
  const featuredIds = new Set(featured.map(prospect => prospect.id));
  const nextStart = ordered.find(prospect => !featuredIds.has(prospect.id));
  const draftedRoles = new Set(draftCounts.map(pick => pick.position));
  const unscouted = featured.filter(prospect => !prospect.scouted);
  const suggested = scoutingPoints > 0
    ? unscouted.find(prospect => !draftedRoles.has(prospect.position)) ?? unscouted[0]
    : undefined;

  return (
    <div className="guided-board" id="prospect-choices">
      <div className="guided-heading">
        <div>
          <h2>Available prospects</h2>
          <p>Open a profile to see what the player does on the field. Spend one scouting point for a playing-time estimate, or review a player with the information you have.</p>
        </div>
        {nextStart && (
          <button className="btn small" disabled={busy} onClick={() => setStartId(nextStart.id)}>
            <Shuffle size={15} />Different profiles
          </button>
        )}
      </div>
      <details className="blind-disclosure">
        <summary>How do I read these stats?</summary>
        <p>A lower 40-yard time means a faster sprint. Height and weight describe size. The numbers are ranges for a group of players. Scouting estimates the group’s chance of reaching 200 plays in their first NFL season.</p>
      </details>
      <div className="guided-cards">
        {featured.map(prospect => {
          const studied = !!prospect.scouted;
          const suggestedScout = prospect.id === suggested?.id;
          return (
            <article className={`guide-card${studied ? ' studied' : ''}${suggestedScout ? ' suggested' : ''}`} key={prospect.id}>
              <div className="guide-card-top">
                <span className="pixel-position">{prospect.position}</span>
                <span className="mono">{prospect.blindName || 'Blind prospect'}</span>
                {board.includes(prospect.id) && <Bookmark size={16} fill="currentColor" aria-label="On your shortlist" />}
              </div>
              <h3>{positionNames[prospect.position] || prospect.position}</h3>
              <p className="guide-role">{positionHelp[prospect.position]?.replace(/^.*? — /, '') || 'This role follows the shared scouting group.'}</p>
              <div className="guide-range-label">Shared group ranges</div>
              <div className="guide-measurements">
                <div><span>Height · in</span><strong>{measurement(prospect, 'height', false)}</strong></div>
                <div><span>Weight · lb</span><strong>{measurement(prospect, 'weight', false)}</strong></div>
                <div><span>40 yards · sec</span><strong>{measurement(prospect, 'forty', false)}</strong></div>
              </div>
              <div className="guide-projection">
                <span>Rookie playing-time outlook</span>
                <strong>{studied && prospect.projection ? roleLabel(prospect) : studied ? 'Unavailable' : 'Not scouted yet'}</strong>
                <p>
                  {studied ? 'Group chance of 200+ plays in the first season.'
                    : suggestedScout ? 'Start here to see what a report adds.'
                    : 'Scouting unlocks the same report for matching profiles.'}
                  {studied && (prospect.projection?.fallback || prospect.projection?.supported === false)
                    && <span className="guide-fallback">Limited evidence · fallback estimate</span>}
                </p>
              </div>
              <div className="guide-card-actions">
                <button className={`btn${suggestedScout ? ' scout-highlight' : ''}`} disabled={busy || studied || scoutingPoints < 1} onClick={() => onScout(prospect.id)}>
                  {studied ? <Check size={15} /> : <Eye size={15} />}
                  {studied ? 'Scouted' : scoutingPoints < 1 ? 'No points left' : 'Scout · 1 point'}
                </button>
                <button className={`btn${myTurn ? ' primary' : ''}`} disabled={busy} onClick={() => onDetail(prospect.id)}>
                  {myTurn ? 'Review & pick' : 'View profile'}<ArrowRight size={15} />
                </button>
              </div>
              <label className="guide-compare">
                <input type="checkbox" checked={compareIds.includes(prospect.id)} disabled={compareIds.length >= 3 && !compareIds.includes(prospect.id)} onChange={() => onCompare(prospect.id)} />
                Compare {prospect.blindName || 'this profile'}
              </label>
            </article>
          );
        })}
      </div>
      {!featured.length && <p className="draft-empty">No available profiles match. Choose another role or clear your search.</p>}
      <div className="guided-footer">
        {draftCounts.length > 0 && <p>Your class: {draftCounts.map(pick => `${pick.count} ${positionNames[pick.position] || pick.position}`).join(' · ')}</p>}
        {prospects.length > 3 && (
          <button className="text-button" onClick={() => setCount(current => current === 3 ? 6 : 3)}>
            {count === 3 ? `Show ${Math.min(6, prospects.length)} profiles` : 'Back to three'}<ArrowRight size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
