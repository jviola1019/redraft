import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { DatabaseSync } from 'node:sqlite';
import { after, test } from 'node:test';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
import { cleanup, engine, loadScenario, root, sim, supportedYears } from '../runtime_loader.mjs';
import { scouting } from '../rubric_multiday/runtime.mjs';

after(cleanup);

function source(relativePath, dependencies, DateClass) {
  const { outputText } = ts.transpileModule(readFileSync(`${root}/${relativePath}`, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  });
  const initialize = runInNewContext(`(function (exports, require) { ${outputText}\n })`, {
    Date: DateClass, Request, Response, console, crypto, process, TextEncoder, TextDecoder, URL,
  }, { filename: relativePath });
  const exports = {};
  const load = createRequire(import.meta.url);
  initialize(exports, key => Object.hasOwn(dependencies, key) ? dependencies[key] : load(key));
  return exports;
}

function asD1(database) {
  return {
    prepare(sql) {
      const statement = database.prepare(sql);
      return { bind: (...values) => ({
        first: async () => statement.get(...values) ?? null,
        run: async () => ({ meta: { changes: statement.run(...values).changes } }),
      }) };
    },
    async batch(statements) {
      database.exec('BEGIN');
      try {
        const results = [];
        for (const statement of statements) results.push(await statement.run());
        database.exec('COMMIT');
        return results;
      } catch (error) {
        database.exec('ROLLBACK');
        throw error;
      }
    },
  };
}

const { fixtures } = JSON.parse(readFileSync(new URL('../rubric_multiday/fixtures.json', import.meta.url)));
const { days } = JSON.parse(readFileSync(new URL('./feasibility.json', import.meta.url)));

for (const [index, config] of fixtures.entries()) {
  for (const direction of ['up', 'down']) {
    test(`Daily POST ${config.date} ${config.team} trade ${direction} matches the engine`, async () => {
      const database = new DatabaseSync(':memory:');
      try {
        const now = `${config.date}T12:00:00.000Z`;
        class FrozenDate extends Date {
          constructor(...args) { super(...(args.length ? args : [now])); }
          static now() { return Date.parse(now); }
        }
        database.exec(readFileSync(`${root}/drizzle/0000_spotty_patriot.sql`, 'utf8'));
        database.prepare('INSERT INTO daily_challenges (date,config,created_at) VALUES (?,?,?)')
          .run(config.date, JSON.stringify(config), now);
        const route = source('app/api/game/route.ts', {
          'cloudflare:workers': { env: { DB: asD1(database) } },
          '@/app/chatgpt-auth': { getChatGPTUser: async () => ({ userId: 'isolated-trade-audit' }) },
          '@/lib/request-body': source('lib/request-body.ts', {}, FrozenDate),
          '@/lib/server-data': { getScenario: loadScenario, years: supportedYears },
          '@/lib/engine': engine,
          '@/lib/simulation': sim,
          '@/lib/scouting': scouting,
        }, FrozenDate);
        const market = days[index].markets[direction];
        const post = async (payload, status) => {
          const request = new Request('https://isolated-redraft.invalid/api/game', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...payload, requestId: crypto.randomUUID() }),
          });
          const response = await route.POST(request);
          const body = await response.json();
          assert.equal(response.status, status, JSON.stringify(body).slice(0, 300));
          return body;
        };
        let { game } = await post({ action: 'new', mode: 'daily' }, 201);
        const base = action => ({ action, id: game.id, revision: game.revision });
        if (direction === 'down') ({ game } = await post({ ...base('advance'), pace: 'user' }, 200));
        assert.equal(game.selections.length, market.selectionCount);
        const stored = () => database.prepare('SELECT state, revision FROM game_runs WHERE id=?').get(game.id);
        const previous = stored();
        const send = (terms, accept, status) => post({ ...base('trade'), ...terms, accept }, status);

        if (market.exampleDecline) {
          const { offer, evaluation } = market.exampleDecline;
          const quote = await send(offer, false, 200);
          assert.deepEqual(quote.tradeEvaluation, evaluation);
          assert.deepEqual(await send(offer, true, 400), { error: evaluation.reason });
          assert.deepEqual(stored(), previous);
        }
        if (market.chosen) {
          const { offer, evaluation } = market.chosen;
          assert.deepEqual((await send(offer, false, 200)).tradeEvaluation, evaluation);
          assert.deepEqual(stored(), previous);
          const accepted = await send(offer, true, 200);
          assert.deepEqual(accepted.tradeEvaluation, evaluation);
          const saved = JSON.parse(stored().state);
          const expected = engine.applyTrade(JSON.parse(previous.state), offer, loadScenario(config.year).dataset);
          assert.deepEqual(saved.picks, expected.picks);
          assert.deepEqual(saved.selections, expected.selections);
          assert.deepEqual(saved.trades, expected.trades);
          assert.equal(saved.revision, previous.revision + 1);
        }
      } finally {
        database.close();
      }
    });
  }
}
