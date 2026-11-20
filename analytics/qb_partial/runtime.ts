import strict from '../five_year_strict_2018.json';
import { isPlayableProspect, positionGroup, probability } from '../../lib/engine';
import { getScenario } from '../../lib/server-data';
import { donorSeasonExposure } from '../../lib/simulation';

const baseline = strict.donors.filter(donor => donor.position === 'QB');
const origins = [2022, 2023, 2024, 2025].map(year => {
    const { dataset, models, scoutingPolicy } = getScenario(year);
    const prospects = dataset.prospects
        .filter(prospect => positionGroup(prospect.position) === 'QB' && isPlayableProspect(prospect))
        .map(prospect => ({
            id: prospect.id,
            name: prospect.name,
            school: prospect.college,
            availableBy: prospect.availableBy,
            probability: probability(prospect, models),
            profile: scoutingPolicy.profiles[prospect.id].groupKey,
        }));
    const baselineExposure = baseline.map(donor => donor.snaps.map((snaps, age) =>
        donorSeasonExposure(snaps, donor.games[age], year + age)));
    return {
        year, cutoff: dataset.metadata.informationCutoff, modelVersion: models.version,
        baselineExposure, prospects,
    };
});
process.stdout.write(JSON.stringify({ strictCutoff: strict.cutoff, baseline, origins }));
