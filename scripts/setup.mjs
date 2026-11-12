/** Portable, non-destructive dependency setup. Does not configure hosted identity. */
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {existsSync} from 'node:fs';
import path from 'node:path';
process.chdir(fileURLToPath(new URL('..',import.meta.url)));
const args=new Set(process.argv.slice(2));
if([...args].some(a=>!['--python','--help'].includes(a)))throw Error('Usage: node scripts/setup.mjs [--python]');
if(args.has('--help')){console.log('Install pinned JavaScript dependencies and run domain tests. --python also creates .venv and installs pinned analytics dependencies. Hosted identity/D1 setup is separate; see INSTALL.md.');process.exit(0);}
const [major]=process.versions.node.split('.').map(Number);
if(major<24)throw Error('Node 24 or newer is required.');
function run(cmd,argv){const r=spawnSync(cmd,argv,{stdio:'inherit',shell:process.platform==='win32'&&cmd==='pnpm'});if(r.error)throw r.error;if(r.status!==0)process.exit(r.status??1);}
run('pnpm',['install','--frozen-lockfile']);
run(process.execPath,['tests/run.mjs']);
if(args.has('--python')){
 const py=process.platform==='win32'?'python':'python3';
 if(!existsSync('.venv'))run(py,['-m','venv','.venv']);
 const executable=path.resolve('.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
 run(executable,['-m','pip','install','-r','analytics/requirements.txt']);
}
console.log('Dependency setup and domain tests completed. This does not certify forecasts or start a public server.');
