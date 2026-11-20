import { ExternalLink } from 'lucide-react';
import { getHistoricalPersonnel } from '@/lib/historical-personnel';

const dateFormat = new Intl.DateTimeFormat('en-US', {
  month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC',
});

function formatDate(date: string) {
  return dateFormat.format(new Date(date));
}

export default function HistoricalPersonnel({ draftYear, teamId }: { draftYear: number; teamId: string }) {
  const snapshot = getHistoricalPersonnel(draftYear, teamId);
  if (!snapshot) return null;

  return (
    <section className="space-bottom" aria-label="Pre-draft personnel and coaching">
      <p className="context-definition">
        Selected announcements available through <time dateTime={snapshot.through}>{formatDate(snapshot.through)}</time>.
        Full roster membership, starting roles, and formation usage are unverified.
      </p>
      <div className="context-groups">
        {snapshot.groups.map(group => (
          <section className="context-group" key={group.title}>
            <header><h3>{group.title}</h3></header>
            <ol>
              {group.facts.map(fact => (
                <li key={fact.label}>
                  <div>
                    <strong>{fact.label}</strong>
                    <p className="small-copy">{fact.detail}</p>
                    <a className="text-button" href={fact.url} target="_blank" rel="noreferrer">
                      {fact.publisher} · <time dateTime={fact.publishedOn}>{formatDate(fact.publishedOn)}</time>
                      <ExternalLink size={12} aria-hidden="true" />
                    </a>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        ))}
      </div>
    </section>
  );
}
