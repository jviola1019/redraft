/** Real route/auth/engine integration. Only Next header context and D1 transport are adapted. */
import assert from 'node:assert/strict';
import { AsyncLocalStorage } from 'node:async_hooks';
import { DatabaseSync } from 'node:sqlite';
import { registerHooks } from 'node:module';
import { readFileSync, readdirSync, existsSync, mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir, cpus, platform, arch } from 'node:os';
import { resolve, dirname, extname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash, randomUUID } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import ts from 'typescript';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
process.chdir(root);
process.env.NODE_ENV = 'production';
const origin = 'https://redraft.integration.test', scratch = mkdtempSync(join(tmpdir(), 'redraft-api-')), databasePath = join(scratch, 'integration.sqlite');
const context = new AsyncLocalStorage();
globalThis.__redraftHeadersContext = context;
globalThis.__redraftTestEnv = {};
const tracked = ['app/api/game/route.ts', 'lib/scouting.ts', 'lib/engine.ts', 'lib/simulation.ts', 'lib/server-data.ts', 'analytics/model.json', 'analytics/five_year_strict_2018.json', 'analytics/scoring_recalibration.json', 'data/clean/team_context_2018.json', 'data/clean/team_context_source_manifest.json', 'data/processed/scenario-2018.json', 'tests/api.integration.mjs', ...readdirSync('drizzle').filter(f => f.endsWith('.sql')).sort().map(f => 'drizzle/' + f)];
const hashes = () => Object.fromEntries(tracked.map(f => [f, createHash('sha256').update(readFileSync(f)).digest('hex')]));
const sourceHashes = hashes();
class D1SQLite {
    constructor(file) { this.sql = new DatabaseSync(file); this.sql.exec('PRAGMA foreign_keys=ON'); }
    prepare(query) { return new D1Statement(this, query, []); }
    async batch(statements) { this.sql.exec('BEGIN IMMEDIATE'); try {
        const result = statements.map(s => s.execute());
        this.sql.exec('COMMIT');
        return result;
    }
    catch (e) {
        this.sql.exec('ROLLBACK');
        throw e;
    } }
    async exec(query) { this.sql.exec(query); return { count: 1, duration: 0 }; }
    close() { this.sql.close(); }
}
class D1Statement {
    constructor(db, query, values) { this.db = db; this.query = query; this.values = values; }
    bind(...values) { return new D1Statement(this.db, this.query, values); }
    execute() { const start = performance.now(), results = this.db.sql.prepare(this.query).all(...this.values), meta = this.db.sql.prepare('SELECT changes() AS changes,last_insert_rowid() AS last_row_id').get(); return { success: true, results, meta: { changes: Number(meta.changes), last_row_id: Number(meta.last_row_id), duration: performance.now() - start } }; }
    async first(column) { const row = this.execute().results[0] ?? null; return column ? (row?.[column] ?? null) : row; }
    async all() { return this.execute(); }
    async run() { return this.execute(); }
    async raw() { return this.execute().results.map(Object.values); }
}
let database = new D1SQLite(databasePath);
globalThis.__redraftTestEnv.DB = database;
const migrations = readdirSync('drizzle').filter(f => f.endsWith('.sql')).sort();
assert.ok(migrations.length);
for (const file of migrations)
    database.sql.exec(readFileSync(join('drizzle', file), 'utf8'));
function findModule(path) { return [path, `${path}.ts`, `${path}.tsx`, `${path}.mjs`, `${path}.js`, `${path}.json`, join(path, 'index.ts')].find(existsSync); }
registerHooks({
    resolve(specifier, ctx, next) {
        const mocks = { 'cloudflare:workers': 'cloudflare', 'next/headers': 'headers', 'next/navigation': 'navigation', 'server-only': 'marker' };
        if (mocks[specifier])
            return { url: `redraft-test:${mocks[specifier]}`, shortCircuit: true };
        if (specifier.startsWith('@/')) {
            const path = findModule(join(root, specifier.slice(2)));
            if (!path)
                throw Error(`Missing ${specifier}`);
            return { url: pathToFileURL(path).href, shortCircuit: true };
        }
        if (specifier.startsWith('.') && ctx.parentURL?.startsWith(pathToFileURL(root).href) && !ctx.parentURL.includes('/node_modules/')) {
            const path = findModule(resolve(dirname(fileURLToPath(ctx.parentURL)), specifier));
            if (path)
                return { url: pathToFileURL(path).href, shortCircuit: true };
        }
        return next(specifier, ctx);
    },
    load(url, ctx, next) {
        const mocks = { cloudflare: 'export const env=globalThis.__redraftTestEnv;', headers: 'export async function headers(){return globalThis.__redraftHeadersContext.getStore()??new Headers();}', navigation: 'export function redirect(path){throw Error("Redirect: "+path);}', marker: 'export {};' };
        if (url.startsWith('redraft-test:'))
            return { format: 'module', source: mocks[url.slice(13)], shortCircuit: true };
        if (url.startsWith(pathToFileURL(root).href) && !url.includes('/node_modules/')) {
            const file = fileURLToPath(url), extension = extname(file);
            if (extension === '.ts' || extension === '.tsx')
                return { format: 'module', source: ts.transpileModule(readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX }, fileName: file }).outputText, shortCircuit: true };
            if (extension === '.json')
                return { format: 'module', source: `export default ${readFileSync(file, 'utf8')};`, shortCircuit: true };
        }
        return next(url, ctx);
    }
});
const { GET, POST } = await import(pathToFileURL(join(root, 'app/api/game/route.ts')).href);
const dataset = JSON.parse(readFileSync('data/processed/scenario-2018.json', 'utf8'));
const developmentModel = JSON.parse(readFileSync('analytics/five_year_strict_2018.json', 'utf8'));
const { positionGroup } = await import(pathToFileURL(join(root, 'lib/engine.ts')).href);
const cases = [], started = performance.now(), nativeDate = Date, quick = process.argv.includes('--quick');
let requests = 0, maximumResponseBytes = 0;
async function call(method, owner, { body, action = 'bootstrap', id, headers: extra = {}, rawBody } = {}) {
    requests++;
    const url = new URL('/api/game', origin);
    if (method === 'GET') {
        url.searchParams.set('action', action);
        if (id)
            url.searchParams.set('id', id);
    }
    const headers = new Headers(extra);
    if (owner) {
        headers.set('oai-authenticated-user-id', owner);
        headers.set('oai-authenticated-user-email', `${owner}@example.invalid`);
    }
    if (method === 'POST') {
        if (!headers.has('origin'))
            headers.set('origin', origin);
        if (!headers.has('content-type'))
            headers.set('content-type', 'application/json');
    }
    const request = new Request(url, { method, headers, ...(method === 'POST' ? { body: rawBody ?? JSON.stringify(body) } : {}) });
    const response = await context.run(headers, () => method === 'POST' ? POST(request) : GET(request)), text = await response.text();
    maximumResponseBytes = Math.max(maximumResponseBytes, new TextEncoder().encode(text).length);
    return { status: response.status, data: JSON.parse(text), headers: response.headers };
}
async function expect(method, owner, options, status = 200) { const result = await call(method, owner, options); assert.equal(result.status, status, JSON.stringify(result.data)); return result.data; }
async function check(name, fn) { const start = performance.now(); try {
    await fn();
    const row = { name, status: 'passed', durationMs: Math.round((performance.now() - start) * 100) / 100 };
    cases.push(row);
    console.log(`PASS ${name} (${row.durationMs} ms)`);
}
catch (e) {
    cases.push({ name, status: 'failed', message: e.message });
    throw e;
} }
const newPayload = (mode = 'historical', extra = {}) => ({ action: 'new', mode, requestId: randomUUID(), ...extra });
const mutation = (view, action, extra = {}) => ({ action, id: view.game.id, revision: view.game.revision, requestId: randomUUID(), ...extra });
const mutate = (owner, view, action, extra = {}) => expect('POST', owner, { body: mutation(view, action, extra) });
const load = (owner, id) => expect('GET', owner, { action: 'load', id });
const one = (query, ...values) => database.sql.prepare(query).get(...values);
const stored = id => JSON.parse(one('SELECT state FROM game_runs WHERE id=?', id).state);
const restore = (id, state) => database.sql.prepare('UPDATE game_runs SET state=? WHERE id=?').run(JSON.stringify(state), id);
function assertNoIds(view) { const text = JSON.stringify(view); assert.ok(!text.includes('p2018-'), 'Canonical player hashes leaked.'); assert.ok(!text.includes('blindSalt'), 'Private salt leaked.'); for (const p of view.prospects ?? [])
    assert.match(p.id, /^bp_[a-f0-9]{32}$/); }
function assertBlind(view) { assertNoIds(view); assert.equal(view.game.identityRevealed, false); assert.equal(view.historicalSelections, undefined); for (const p of view.prospects) {
    assert.ok(!dataset.prospects.some(raw => raw.name === p.name), `Name leaked: ${p.name}`);
    assert.equal(p.college, 'Hidden until reveal');
    for (const f of ['heightIn', 'weightLb', 'forty', 'bench', 'verticalIn', 'broadJumpIn', 'cone', 'shuttle'])
        assert.equal(p[f], null, `Exact ${f} leaked.`);
    assert.equal(p.source, undefined);
    assert.equal(p.availableBy, undefined);
    assert.equal(p.eligibilitySource, undefined);
    assert.ok(p.displayMeasurements && Object.values(p.displayMeasurements).every(v => typeof v === 'string'));
    if (!p.scouted)
        assert.equal(p.projection.roleProbability, null);
} }
const signature = p => JSON.stringify([p.position, p.displayMeasurements]);
async function finishDraft(owner, initial, preferred = []) { let view = initial, turns = 0; while (view.game.status === 'drafting') {
    assert.ok(turns++ < 520);
    const pick = view.game.picks[view.game.selections.length];
    if (pick.owner !== view.game.team)
        view = await mutate(owner, view, 'advance', { pace: 'user' });
    else {
        const chosen = new Set(view.game.selections.map(p => p.prospectId)), id = preferred.find(id => !chosen.has(id)) ?? view.prospects.find(p => !chosen.has(p.id))?.id;
        assert.ok(id);
        view = await mutate(owner, view, 'pick', { prospectId: id });
    }
    assertNoIds(view);
    if (view.game.mode === 'daily')
        assertBlind(view);
} assert.equal(view.game.status, 'ready'); assert.equal(view.game.selections.length, 256); assert.equal(new Set(view.game.selections.map(p => p.prospectId)).size, 256); assert.equal(new Set(view.game.selections.map(p => p.team)).size, 32); return view; }
async function finishSimulation(owner, initial, reopen = false) { let view = initial, steps = 0; while (view.game.status !== 'complete') {
    const before = view.game.results?.replicates.length ?? 0;
    view = await mutate(owner, view, 'simulate');
    const count = view.game.results.replicates.length;
    assert.equal(count, Math.min(256, before + 4));
    assertNoIds(view);
    if (view.game.status === 'simulating')
        assert.ok(view.game.results.replicates.every(r => r.baseline.seasons.length === 0 && r.alternate.seasons.length === 0));
    if (view.game.mode === 'daily')
        assertBlind(view);
    steps++;
    assert.ok(steps <= 64);
    if (reopen && steps === 3) {
        const id = view.game.id, revision = view.game.revision;
        database.close();
        database = new D1SQLite(databasePath);
        globalThis.__redraftTestEnv.DB = database;
        view = await load(owner, id);
        assert.equal(view.game.revision, revision);
        assert.equal(view.game.results.replicates.length, count);
    }
    if (steps % 16 === 0)
        console.log(`PROGRESS ${owner}: ${count}/256 paired runs`);
} assert.equal(view.game.results.summary.samples, 256); return view; }
function setClock(iso) { const fixed = nativeDate.parse(iso); globalThis.Date = class extends nativeDate {
    constructor(...args) { if (args.length)
        super(...args);
    else
        super(fixed); }
    static now() { return fixed; }
}; }
let historical, dailyA, dailyB, peer, failure;
try {
    await check('five-year donor labels precede the draft and do not claim independent validation', async () => {
        assert.ok(Date.parse(developmentModel.cutoff) <= Date.parse(dataset.metadata.informationCutoff));
        assert.ok(developmentModel.cohorts.every(year => year + 4 < 2018));
        assert.ok(Object.keys(developmentModel.sourceCoverage).every(year => Number(year) < 2018));
        assert.equal(developmentModel.validation.chronologicallyValidatedFor2018, false);
        assert.ok(developmentModel.donors.length > 0);
        for (const donor of developmentModel.donors) {
            assert.equal(donor.games.length, 5);
            assert.equal(donor.snaps.length, 5);
            assert.ok(donor.games.every(n => Number.isInteger(n) && n >= 0 && n <= 16));
            assert.ok(donor.snaps.every(n => Number.isFinite(n) && n >= 0));
        }
    });
    await check('auth, CSRF, strict schema and body-size limits', async () => {
        await expect('POST', null, { body: newPayload() }, 401);
        await expect('GET', null, { action: 'history' }, 401);
        await expect('POST', 'security', { body: newPayload(), headers: { origin: 'https://untrusted.invalid' } }, 403);
        await expect('POST', 'security', { body: newPayload(), headers: { 'sec-fetch-site': 'cross-site' } }, 403);
        await expect('POST', 'security', { body: newPayload(), headers: { 'content-type': 'text/plain' } }, 415);
        await expect('POST', 'security', { rawBody: '{' }, 400);
        await expect('POST', 'security', { rawBody: ' '.repeat(16001) }, 413);
        await expect('POST', 'security', { body: { ...newPayload(), score: 100 } }, 400);
        await expect('POST', 'security', { body: { action: 'new', mode: 'historical' } }, 400);
        await expect('POST', 'security', { body: newPayload('historical', { year: 2020 }) }, 400);
        await expect('POST', 'security', { body: newPayload('historical', { team: 'ZZZ' }) }, 400);
    });
    await check('versioned creation and request replay', async () => {
        const bootstrap = await expect('GET', 'historical-owner');
        assert.deepEqual(bootstrap.years, [2018]);
        assert.equal(bootstrap.teams.length, 32);
        assert.equal(bootstrap.teamContexts.length, 32);
        assert.equal(bootstrap.teamContextMetadata.observedSeason, 2017);
        assert.equal(bootstrap.teamContextMetadata.artifactSha256, sourceHashes['data/clean/team_context_2018.json']);
        assert.ok(bootstrap.teamContexts.every(t => t.scheme === null && t.draftDayRoster === null && t.groups.every(g => g.topContributors === undefined)));
        assert.equal(bootstrap.methodology.ensembleSize, 256);
        const payload = newPayload('historical', { team: 'CLE', seed: 'integration-seed' });
        historical = await expect('POST', 'historical-owner', { body: payload }, 201);
        const replay = await expect('POST', 'historical-owner', { body: payload });
        assert.equal(replay.game.id, historical.game.id);
        assert.equal(replay.game.revision, 0);
        assert.equal(one('SELECT count(*) AS n FROM game_runs WHERE owner=?', 'historical-owner').n, 1);
        assert.equal(historical.prospects.length, 336);
        assert.equal(historical.selectedTeamContext.teamId, 'CLE');
        assert.equal(historical.selectedTeamContext.priorSeason, 2017);
        assert.ok(historical.selectedTeamContext.groups.every(g => Array.isArray(g.topContributors) && g.topContributors.length <= 4));
        assert.match(historical.game.modelVersion, /prior-utilization-policy-v1:.*\+scoring-trailing3-v1$/);
        assertBlind(historical);
        const state = stored(historical.game.id);
        assert.equal(state.modelVersion, bootstrap.methodology.version);
        assert.equal(state.datasetVersion, bootstrap.methodology.datasetVersion);
        assert.equal(state.scoutingVersion, bootstrap.methodology.scoutingVersion);
        assert.equal(state.ensembleSize, 256);
    });
    await check('owner isolation, aliases and canonical identifier rejection', async () => {
        await expect('GET', 'other-owner', { action: 'load', id: historical.game.id }, 404);
        await expect('POST', 'other-owner', { body: mutation(historical, 'save') }, 404);
        const other = await expect('POST', 'alias-owner', { body: newPayload('historical', { team: 'CLE', seed: 'integration-seed' }) }, 201);
        assert.equal(historical.prospects.filter(p => other.prospects.some(q => q.id === p.id)).length, 0);
        assert.deepEqual((await load('historical-owner', historical.game.id)).prospects.map(p => p.id), historical.prospects.map(p => p.id));
        const canonical = dataset.prospects.find(p => p.eligibilitySource === 'combine-participant').id;
        for (const action of ['pick', 'scout'])
            await expect('POST', 'historical-owner', { body: mutation(historical, action, { prospectId: canonical }) }, 400);
        await expect('POST', 'historical-owner', { body: mutation(historical, 'board', { prospectIds: [canonical] }) }, 400);
        await expect('POST', 'historical-owner', { body: mutation(historical, 'scout', { prospectId: other.prospects[0].id }) }, 400);
        const response = await call('GET', 'historical-owner', { action: 'load', id: historical.game.id });
        assert.match(response.headers.get('cache-control'), /no-store/);
        assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
    });
    await check('group scouting costs once and preserves blind ranges', async () => {
        const chosen = historical.prospects[0], payload = mutation(historical, 'scout', { prospectId: chosen.id });
        historical = await expect('POST', 'historical-owner', { body: payload });
        assertBlind(historical);
        assert.equal(historical.game.scoutingPoints, 11);
        assert.equal(historical.game.scouted.length, 1);
        const unlocked = historical.prospects.filter(p => p.scouted);
        assert.ok(unlocked.length >= 5);
        peer = unlocked.find(p => p.id !== chosen.id).id;
        for (const p of unlocked)
            if (p.position !== 'ST') {
                assert.match(p.projection.roleProbabilityLabel, /^\d+–\d+%$/);
                const [lo, hi] = p.projection.roleProbabilityLabel.match(/\d+/g).map(Number);
                assert.equal(p.projection.roleProbability, (lo + hi) / 200);
            }
        const replay = await expect('POST', 'historical-owner', { body: payload });
        assert.equal(replay.game.revision, historical.game.revision);
        assert.equal(replay.game.scoutingPoints, 11);
        await expect('POST', 'historical-owner', { body: mutation(historical, 'scout', { prospectId: peer }) }, 400);
        await expect('POST', 'historical-owner', { body: { ...payload, prospectId: peer } }, 409);
        assert.equal(stored(historical.game.id).scoutingPoints, 11);
    });
    await check('stale revision and concurrent CAS cannot lose updates', async () => {
        const available = historical.prospects.filter(p => !p.scouted), a = available[0], b = available.find(p => signature(p) !== signature(a));
        assert.ok(b);
        await expect('POST', 'historical-owner', { body: { ...mutation(historical, 'save'), revision: historical.game.revision - 1 } }, 409);
        const responses = await Promise.all([a, b].map(p => call('POST', 'historical-owner', { body: mutation(historical, 'scout', { prospectId: p.id }) })));
        assert.deepEqual(responses.map(r => r.status).sort(), [200, 409]);
        historical = await load('historical-owner', historical.game.id);
        assert.equal(historical.game.scoutingPoints, 10);
        assert.equal(historical.game.scouted.length, 2);
    });
    await check('counteroffers and accepted trades conserve ownership', async () => {
        const last = historical.game.picks.filter(p => p.owner === 'CLE').at(-1).overall, before = historical.game.revision;
        const declined = await expect('POST', 'historical-owner', { body: mutation(historical, 'trade', { target: 'NYG', give: [last], receive: [2], accept: false }) });
        assert.equal(declined.tradeEvaluation.accepted, false);
        assert.ok(declined.tradeEvaluation.counter);
        assert.equal(declined.game.revision, before);
        const offer = { target: 'NYG', give: [1], receive: [2], accept: false }, quoted = await expect('POST', 'historical-owner', { body: mutation(historical, 'trade', offer) });
        assert.equal(quoted.tradeEvaluation.accepted, true);
        historical = await mutate('historical-owner', historical, 'trade', { ...offer, accept: true });
        assert.equal(historical.game.picks[0].owner, 'NYG');
        assert.equal(historical.game.picks[1].owner, 'CLE');
        assert.equal(historical.game.trades.length, 1);
    });
    await check('historical full draft, reveal and persisted recovery', async () => {
        historical = await finishDraft('historical-owner', historical, [peer]);
        assert.equal(historical.game.identityRevealed, true);
        assert.equal(historical.prospects.length, 375);
        assert.equal(historical.historicalSelections.length, 256);
        assertNoIds(historical);
        assert.ok(historical.prospects.every(p => dataset.prospects.some(raw => raw.name === p.name)));
        const saved = await mutate('historical-owner', historical, 'save');
        historical = await load('historical-owner', saved.game.id);
        assert.equal(historical.game.revision, saved.game.revision);
        assert.deepEqual(historical.game.selections, saved.game.selections);
    });
    await check('retired source versions allow review but block mutations', async () => {
        const original = stored(historical.game.id);
        restore(historical.game.id, { ...original, modelVersion: 'retired-model-fixture' });
        const old = await load('historical-owner', historical.game.id);
        assert.ok(old.compatibilityWarning);
        assert.ok(old.prospects.every(p => p.projection.roleProbability === null));
        await expect('POST', 'historical-owner', { body: mutation(old, 'save') }, 409);
        restore(historical.game.id, original);
        historical = await load('historical-owner', historical.game.id);
    });
    if (!quick)
        await check('historical 256-pair simulation survives a database reopen', async () => {
            historical = await finishSimulation('historical-owner', historical, true);
            const full = historical.game.results.replicates[0];
            assert.equal(full.alternate.seasons.length, 5);
            assert.equal(full.baseline.seasons.length, 5);
            for (const s of full.alternate.seasons) {
                assert.equal(s.teams.reduce((n, t) => n + t.wins, 0), s.teams.reduce((n, t) => n + t.losses, 0));
                assert.equal(s.teams.filter(t => t.champion).length, 1);
            }
            const byId = new Map(historical.prospects.map(p => [p.id, p]));
            for (const player of full.alternate.seasons[0].players) {
                const position = positionGroup(byId.get(player.prospectId).position), group = ['K', 'P', 'LS'].includes(position) ? 'ST' : position;
                const trajectory = full.alternate.seasons.map(season => season.players.find(p => p.prospectId === player.prospectId).games);
                assert.ok(developmentModel.donors.some(d => d.position === group && JSON.stringify(d.games) === JSON.stringify(trajectory)), 'Five-year availability must retain one whole observed donor trajectory.');
                if (full.baseline.seasons[0].players.some(p => p.prospectId === player.prospectId))
                    assert.deepEqual(full.baseline.seasons.map(season => season.players.find(p => p.prospectId === player.prospectId).games), trajectory, 'Common players must retain paired availability random streams.');
            }
            assert.ok(historical.game.results.scoreComponents.find(c => c.name === 'Scouting coverage').score > 0, 'Unlocked group peer should receive scouting coverage.');
            const state = stored(historical.game.id);
            assert.ok(new TextEncoder().encode(JSON.stringify(state)).length < 1800000);
            assert.equal(state.results.replicates.length, 256);
        });
    await check('daily conditions, aliases and one official attempt are shared', async () => {
        await expect('POST', 'daily-a', { body: newPayload('daily', { team: 'CLE' }) }, 400);
        await expect('POST', 'daily-a', { body: newPayload('daily', { seed: 'chosen' }) }, 400);
        dailyA = await expect('POST', 'daily-a', { body: newPayload('daily') }, 201);
        dailyB = await expect('POST', 'daily-b', { body: newPayload('daily') }, 201);
        assertBlind(dailyA);
        assertBlind(dailyB);
        assert.equal(dailyA.game.team, dailyB.game.team);
        assert.deepEqual(dailyA.prospects, dailyB.prospects);
        assert.deepEqual(dailyA.game.picks, dailyB.game.picks);
        assert.equal(stored(dailyA.game.id).seed, stored(dailyB.game.id).seed);
        assert.equal(stored(dailyA.game.id).blindSalt, stored(dailyB.game.id).blindSalt);
        assert.notEqual(dailyA.game.seed, stored(dailyA.game.id).seed);
        const again = await expect('POST', 'daily-a', { body: newPayload('daily') });
        assert.equal(again.game.id, dailyA.game.id);
        assert.equal(one('SELECT count(*) AS n FROM daily_attempts WHERE owner=?', 'daily-a').n, 1);
    });
    await check('identical daily decisions yield identical seven-round drafts', async () => {
        const first = dailyA.prospects[0].id;
        dailyA = await mutate('daily-a', dailyA, 'scout', { prospectId: first });
        dailyB = await mutate('daily-b', dailyB, 'scout', { prospectId: first });
        const peers = dailyA.prospects.filter(p => p.scouted).map(p => p.id);
        dailyA = await finishDraft('daily-a', dailyA, peers);
        dailyB = await finishDraft('daily-b', dailyB, peers);
        assert.deepEqual(dailyA.game.selections, dailyB.game.selections);
        assert.deepEqual(dailyA.game.trades, dailyB.game.trades);
        assertBlind(dailyA);
        assertBlind(dailyB);
    });
    if (!quick)
        await check('daily 256-pair results remain blind with immutable server scores', async () => {
            dailyA = await finishSimulation('daily-a', dailyA);
            dailyB = await finishSimulation('daily-b', dailyB);
            assertBlind(dailyA);
            assertBlind(dailyB);
            assert.equal(dailyA.game.results.decisionScore, dailyB.game.results.decisionScore);
            assert.deepEqual(dailyA.game.results.summary, dailyB.game.results.summary);
            for (const s of dailyA.game.results.replicates[0].baseline.seasons) {
                assert.equal(s.players.length, 0, 'Actual baseline player allocation is sealed until close.');
                assert.equal(s.starPicks.length, 0);
                assert.equal(s.awards.length, 0);
            }
            const leaders = await expect('GET', 'daily-a', { action: 'leaderboard' });
            assert.equal(leaders.leaderboard.length, 2);
            assert.deepEqual(leaders.leaderboard.map(e => e.rank), [1,1], 'Equal official scores share rank.');
            assert.ok(leaders.leaderboard.every(e => Number.isFinite(e.score) && e.score >= 0 && e.score <= 100 && /^GM-/.test(e.alias)));
            assert.equal(one('SELECT count(*) AS n FROM daily_leaderboard_entries WHERE owner=?', 'daily-a').n, 1);
            assert.equal(one('SELECT score FROM daily_leaderboard_entries WHERE owner=?', 'daily-a').score, dailyA.game.results.decisionScore);
            await expect('POST', 'daily-a', { body: { ...mutation(dailyA, 'save'), score: 100 } }, 400);
            const replay = await mutate('daily-a', dailyA, 'simulate');
            assert.equal(replay.game.results.decisionScore, dailyA.game.results.decisionScore);
            assert.equal(one('SELECT count(*) AS n FROM daily_leaderboard_entries WHERE owner=?', 'daily-a').n, 1);
        });
    await check('UTC rollover closes old attempts and reveals completed draft identities', async () => {
        const unfinished = await expect('POST', 'rollover-owner', { body: newPayload('daily') }, 201), today = stored(unfinished.game.id).createdAt.slice(0, 10), tomorrow = new nativeDate(nativeDate.parse(today + 'T00:00:00Z') + 86400000).toISOString();
        setClock(tomorrow);
        try {
            await expect('POST', 'rollover-owner', { body: mutation(unfinished, 'advance', { pace: 'user' }) }, 409);
            const reveal = await load('daily-a', dailyA.game.id);
            assert.equal(reveal.game.identityRevealed, true);
            assert.equal(reveal.historicalSelections.length, 256);
            assert.equal(reveal.prospects.length, 375);
            assert.ok(reveal.prospects.every(p => dataset.prospects.some(raw => raw.name === p.name)));
            const next = await expect('POST', 'rollover-owner', { body: newPayload('daily') }, 201);
            assert.notEqual(next.game.id, unfinished.game.id);
            assert.equal(one('SELECT count(*) AS n FROM daily_attempts WHERE owner=?', 'rollover-owner').n, 2);
            assert.equal((await expect('GET', 'rollover-owner')).daily.date, tomorrow.slice(0, 10));
        }
        finally {
            globalThis.Date = nativeDate;
        }
    });
    await check('frozen daily versions and rate limits are enforced', async () => {
        const date = new nativeDate().toISOString().slice(0, 10), original = one('SELECT config FROM daily_challenges WHERE date=?', date).config;
        database.sql.prepare('UPDATE daily_challenges SET config=? WHERE date=?').run(JSON.stringify({ ...JSON.parse(original), engineVersion: 'retired-engine-fixture' }), date);
        try {
            await expect('POST', 'pinned-owner', { body: newPayload('daily') }, 409);
            assert.equal(JSON.parse(one('SELECT config FROM daily_challenges WHERE date=?', date).config).engineVersion, 'retired-engine-fixture');
        }
        finally {
            database.sql.prepare('UPDATE daily_challenges SET config=? WHERE date=?').run(original, date);
        }
        const minute = Math.floor(nativeDate.now() / 60000);
        database.sql.prepare('INSERT INTO rate_windows(id,count,expires_at) VALUES(?,?,?)').run(`limited-owner:${minute}`, 240, (minute + 2) * 60000);
        await expect('POST', 'limited-owner', { body: newPayload() }, 429);
        assert.equal(one('SELECT count(*) AS n FROM game_runs WHERE owner=?', 'limited-owner').n, 0);
    });
}
catch (e) {
    failure = e;
    console.error('FAIL', e.stack ?? e);
    process.exitCode = 1;
}
finally {
    globalThis.Date = nativeDate;
    const finalHashes = hashes(), sourceChanged = Object.keys(sourceHashes).some(f => sourceHashes[f] !== finalHashes[f]);
    const report = { executedAt: new nativeDate().toISOString(), runtime: { node: process.version, os: platform(), architecture: arch(), cpu: cpus()[0]?.model }, scope: quick ? 'Security and draft flows only; simulation omitted' : 'Full 256-pair historical and two daily participants', method: 'Real route and auth helper through Node registerHooks; SQLite-backed D1 adapter and Next header-context adapter. Not a browser or production Cloudflare test.', migrations, sourceHashes, finalHashes, sourceChangedDuringRun: sourceChanged, cases, passed: cases.filter(c => c.status === 'passed').length, failed: cases.filter(c => c.status === 'failed').length, requests, maximumResponseBytes, durationMs: performance.now() - started, limitations: ['Does not establish Safari/WebKit behavior or production Worker CPU limits.', 'Synthetic identities and disposable SQLite database are isolated test fixtures.'] };
    mkdirSync('tests/results', { recursive: true });
    writeFileSync(`tests/results/api-integration${quick ? '-quick' : ''}.json`, JSON.stringify(report, null, 2) + '\n');
    console.log('API_INTEGRATION_REPORT', JSON.stringify({ passed: report.passed, failed: report.failed, requests, durationMs: Math.round(report.durationMs), sourceChangedDuringRun: sourceChanged }));
    database.close();
    rmSync(scratch, { recursive: true, force: true });
    if (sourceChanged) {
        console.warn('Source changed during execution; repeat on frozen source before claiming final verification.');
        process.exitCode = 1;
    }
}
if (failure)
    throw failure;
