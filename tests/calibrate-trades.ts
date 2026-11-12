import { readFileSync, writeFileSync } from 'node:fs';
import { createGame, autoComplete, RULE_VERSION } from '../lib/engine';
const data = JSON.parse(readFileSync('data/clean/scenario_2018.json', 'utf8')), model = JSON.parse(readFileSync('analytics/model.json', 'utf8'));
function run(rate: number, n: number, prefix: string) { const counts = []; for (let i = 0; i < n; i++) {
    const g = autoComplete(createGame({ team: 'CLE', seed: `${prefix}-${i}` }, data), data, { ...model, tradeArrivalRate: rate });
    counts.push(g.trades.length);
} return { rate, counts, mean: counts.reduce((a, b) => a + b, 0) / counts.length }; }
const prior = [.08, .12, .16].map(rate => run(rate, 8, 'trade-calibration')), selected = run(.10, 8, 'trade-calibration'), validation = run(.10, 16, 'trade-validation');
const report = { historicalTrainYears: [2013, 2017], currentYearPickOnlyCounts: [19, 19, 17, 16, 29], targetMean: 20, candidates: [...prior, selected], selectedArrivalRate: .10, independentSeedsValidation: validation, limitations: ['Frequency calibration matches one prior-cohort first moment only; partners, prices, urgency and acceptance remain heuristic.', 'Historical counts include all teams while simulation reserves the user franchise for user-initiated trades. Fixed-CLE calibration does not establish other-team calibration.', '2018 historical trade counts are held out.'], reproduce: 'Bundle tests/calibrate-trades.ts with esbuild and run from project root. All candidates and validation seeds are rerun.', engineVersion: RULE_VERSION };
console.log(JSON.stringify(report));
writeFileSync('tests/trade-calibration.json', JSON.stringify(report, null, 2));
