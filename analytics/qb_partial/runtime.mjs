import { existsSync, readdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const require = createRequire(import.meta.url);
const root = fileURLToPath(new URL('../../', import.meta.url));
const pnpm = join(root, 'node_modules/.pnpm');
let esbuild;
try {
    esbuild = require('esbuild');
} catch {
    const candidates = readdirSync(pnpm).filter(name => name.startsWith('esbuild@')).sort().reverse();
    const installed = candidates.find(name => existsSync(join(pnpm, name, 'node_modules/esbuild/lib/main.js')));
    if (!installed) throw new Error('Install repository dependencies first.');
    esbuild = require(join(pnpm, installed, 'node_modules/esbuild/lib/main.js'));
}
const { outputFiles } = esbuild.buildSync({
    entryPoints: [fileURLToPath(new URL('./runtime.ts', import.meta.url))],
    tsconfig: join(root, 'tsconfig.json'),
    bundle: true,
    platform: 'node',
    target: 'node22',
    format: 'esm',
    write: false,
});
await import('data:text/javascript;base64,' + Buffer.from(outputFiles[0].contents).toString('base64'));
