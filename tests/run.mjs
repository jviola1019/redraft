import {readdirSync,mkdtempSync,rmSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);let esbuild;
try{esbuild=require('esbuild');}catch{const pnpm=resolve('node_modules/.pnpm'),name=readdirSync(pnpm).filter(n=>n.startsWith('esbuild@')).sort().reverse().find(n=>existsSync(join(pnpm,n,'node_modules/esbuild/lib/main.js')));if(!name)throw Error('Install repository dependencies first.');esbuild=require(join(pnpm,name,'node_modules/esbuild/lib/main.js'));}
const output=mkdtempSync(join(tmpdir(),'redraft-tests-'));
try{const files=readdirSync('tests').filter(n=>n.endsWith('.test.ts'));for(const name of files)esbuild.buildSync({entryPoints:[`tests/${name}`],bundle:true,platform:'node',target:'node22',format:'esm',outfile:join(output,name.replace(/\.ts$/,'.mjs')),logLevel:'warning'});const r=spawnSync(process.execPath,['--test',...files.map(n=>join(output,n.replace(/\.ts$/,'.mjs')))],{stdio:'inherit'});process.exitCode=r.status??1;}finally{rmSync(output,{recursive:true,force:true});}
