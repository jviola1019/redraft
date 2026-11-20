import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { runInNewContext } from 'node:vm';
import { DatabaseSync } from 'node:sqlite';
import ts from 'typescript';
import { engine, sim, loadScenario, root, supportedYears } from '../runtime_loader.mjs';

export const dates = Array.from({ length: 6 }, (_, i) => `2026-11-0${i + 1}`);
const loadRequire = createRequire(import.meta.url);

export function verifyProtocol() {
  const document = readFileSync(new URL('./PROTOCOL.md', import.meta.url));
  const digest = createHash('sha256').update(document).digest('hex');
  if (digest !== '25cd696872473f3c54bedd3270cd86aa1539041185e30f95f0f751802d2764d5') {
    throw Error('Frozen protocol digest changed.');
  }
  return digest;
}

function sourceModule(relativePath, dependencies, DateClass = Date) {
  const source = readFileSync(`${root}/${relativePath}`, 'utf8');
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  });
  const exports = {};
  const resolve = name => Object.hasOwn(dependencies, name) ? dependencies[name] : loadRequire(name);
  const initialize = runInNewContext(`(function (exports, require) { ${outputText}\n })`, {
    Date: DateClass, Request, Response, crypto, console, process, TextEncoder, URL,
  }, { filename: relativePath });
  initialize(exports, resolve);
  return exports;
}

export const scouting = sourceModule('lib/scouting.ts', { './engine': engine });

function asD1(database) {
  return {
    prepare(sql) {
      const statement = database.prepare(sql);
      return {
        bind(...values) {
          return {
            async first() { return statement.get(...values) ?? null; },
            async all() { return { results: statement.all(...values) }; },
            async run() { return statement.run(...values); },
          };
        },
      };
    },
  };
}

export async function generateFixtures() {
  verifyProtocol();
  const database = new DatabaseSync(':memory:');
  try {
    database.exec(readFileSync(`${root}/drizzle/0000_spotty_patriot.sql`, 'utf8'));
    let now;
    class FrozenDate extends Date {
      constructor(...args) { super(...(args.length ? args : [now])); }
      static now() { return new Date(now).getTime(); }
    }
    const route = sourceModule('app/api/game/route.ts', {
      'cloudflare:workers': { env: { DB: asD1(database) } },
      '@/app/chatgpt-auth': { getChatGPTUser: async () => ({ userId: 'isolated-rubric-audit' }) },
      '@/lib/request-body': sourceModule('lib/request-body.ts', {}),
      '@/lib/server-data': { getScenario: loadScenario, years: supportedYears },
      '@/lib/engine': engine,
      '@/lib/simulation': sim,
      '@/lib/scouting': scouting,
    }, FrozenDate);
    for (const date of dates) {
      now = `${date}T12:00:00.000Z`;
      const request = new Request('https://isolated-redraft.invalid/api/game?action=leaderboard');
      for (let pass = 0; pass < 2; pass++) {
        const response = await route.GET(request);
        if (!response.ok) throw Error(`Fixture GET failed for ${date} with HTTP ${response.status}`);
      }
    }
    return database.prepare('SELECT config FROM daily_challenges ORDER BY date').all()
      .map(row => JSON.parse(row.config));
  } finally {
    database.close();
  }
}
