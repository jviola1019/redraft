import source from '@/data/clean/historical_compensatory_slots.json';
import type { Dataset } from './types';

export const orderSnapshot2020 = {
    asOfDate: '2020-04-15',
    draftOpeningDate: '2020-04-23',
    openingOrderComplete: false,
    note: 'The 2020 starting order is as of April 15. The draft opened April 23. New England and Tampa Bay exchanged picks 139 and 241 on April 21, after this snapshot.',
    sources: [
        { title: 'Tennessee Titans April 16 draft release with the April 15 order', url: 'https://static.clubs.nfl.com/image/upload/titans/ff4ybykwg15lmlhb9mne.pdf' },
        { title: 'New England Patriots transaction history, page 331', url: 'https://static.www.nfl.com/image/upload/v1596583660/league/t593ytg5tznazrtqanlu.pdf' },
    ],
};

export function withHistoricalDraftEvidence(dataset: Dataset): Dataset {
    const evidence = source.scenarios.find(record => record.year === dataset.metadata.draftYear);
    const count = dataset.picks.filter(pick => pick.compensatory === true).length;
    if (!evidence) return {
        ...dataset,
        metadata: {
            ...dataset.metadata,
            compensatoryClassification: `${count} compensatory slots identified in the source order.`,
            ...(dataset.metadata.draftYear === 2020 ? { orderSnapshot: orderSnapshot2020 } : {}),
        },
    };

    const roundsByOverall = new Map(dataset.picks.map(pick => [pick.overall, pick.round]));
    const compensatory = new Set<number>();
    if (dataset.metadata.version !== evidence.scenarioVersion || roundsByOverall.size !== evidence.slotCount ||
        dataset.picks.length !== evidence.slotCount || dataset.picks.some(pick => pick.compensatory !== undefined))
        throw new Error(`Compensatory source does not match the ${evidence.year} draft snapshot.`);

    for (const group of evidence.byRound) {
        for (const overall of group.overall) {
            if (roundsByOverall.get(overall) !== group.round || compensatory.has(overall))
                throw new Error(`Invalid compensatory classification for ${evidence.year} pick ${overall}.`);
            compensatory.add(overall);
        }
    }
    if (compensatory.size !== evidence.slotCountCompensatory)
        throw new Error(`Compensatory classification count does not match the ${evidence.year} source.`);

    return {
        ...dataset,
        metadata: {
            ...dataset.metadata,
            compensatoryClassification: `${compensatory.size} compensatory slots verified against official draft materials.`,
            compensatoryEvidence: {
                version: source.version,
                auditedOn: source.auditedOn,
                count: compensatory.size,
                sources: evidence.sources,
            },
        },
        picks: dataset.picks.map(pick => ({ ...pick, compensatory: compensatory.has(pick.overall) })),
    };
}
