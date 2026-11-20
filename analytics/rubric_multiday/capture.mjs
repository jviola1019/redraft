import { writeFileSync } from 'node:fs';
import { cleanup } from '../runtime_loader.mjs';
import { generateFixtures, verifyProtocol } from './runtime.mjs';

try {
  const fixtures = await generateFixtures();
  writeFileSync(new URL('./fixtures.json', import.meta.url), JSON.stringify({
    provenance: 'Authoritative runtime GET /api/game?action=leaderboard on isolated migrated SQLite at noon UTC',
    protocolSha256: verifyProtocol(),
    fixtures,
  }, null, 2) + '\n', { flag: 'wx' });
  console.log(fixtures.map(({ date, year, team }) => ({ date, year, team })));
} finally {
  cleanup();
}
