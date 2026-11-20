import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { loadScenario, cleanup } from '../../analytics/runtime_loader.mjs';
const groups = ['QB','RB','WR','TE','OL','DL','LB','DB'];
const version = 'recognition-2018-v1';
const hash = value => createHash('sha256').update(version + value).digest('hex');
const out = process.argv[2];
if (!out) throw Error('Supply an output directory for the participant forms and separate facilitator key.');
try {
  const {dataset,scoutingPolicy} = loadScenario(2018);
  const eligible = dataset.prospects.filter(p => scoutingPolicy.profiles[p.id] && p.college && p.name);
  const pairs = groups.map((position,index) => {
    const candidates = eligible.filter(p => scoutingPolicy.profiles[p.id].position === position)
      .sort((a,b)=>hash(a.id).localeCompare(hash(b.id)));
    for (const a of candidates) {
      const profile = scoutingPolicy.profiles[a.id];
      const b = candidates.find(p => p.id !== a.id && p.college !== a.college && profile.memberIds.includes(p.id));
      if (b) return {item:index+1,position,profile,players:[a,b]};
    }
    throw Error('No comparable pair for '+position);
  });
  const versioned = {study:version, pairs:pairs.map(({item,position,players})=>({item,position,names:players.map(p=>p.name)}))};
  versioned.keyId = hash(JSON.stringify(versioned));
  mkdirSync(out,{recursive:true});
  writeFileSync(resolve(out,'key.json'),JSON.stringify(versioned,null,2));
  const template = readFileSync(new URL('./form.html',import.meta.url),'utf8');
  for(const form of ['A','B']) {
    const items=pairs.map(({item,position,profile,players})=>({
      item,position,range:profile.probabilityBand?.label??'Unavailable',
      height:profile.displayMeasurements.height,weight:profile.displayMeasurements.weight,
      colleges:(item%2===(form==='A'?1:0))?players.map(p=>p.college):null
    }));
    const payload=JSON.stringify({study:version,keyId:versioned.keyId,form,items}).replaceAll('<','\\u003c');
    writeFileSync(resolve(out,'form-'+form+'.html'),template.replace('/*STUDY_DATA*/null',payload));
  }
} finally { cleanup(); }
