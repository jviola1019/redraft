import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const directory = mkdtempSync(join(tmpdir(), 'redraft-study-'));
let browser;
try {
  execFileSync(process.execPath, ['research/recognition_trial/prepare.mjs', directory]);
  browser = await chromium.launch();
  const page = await browser.newPage({viewport:{width:390,height:844}});
  await page.goto(pathToFileURL(join(directory,'form-A.html')).href);
  await page.getByLabel('How closely do you follow the NFL draft?').selectOption('occasionally');
  await page.getByRole('button',{name:'Begin'}).click();
  for (let index=0; index<8; index++) {
    await page.getByRole('heading',{name:new RegExp('Pair '+(index+1)+' of 8')}).waitFor();
    await page.getByRole('radio').first().check();
    await page.getByRole('button',{name:'Save answer and continue'}).click();
  }
  const event=page.waitForEvent('download');
  await page.getByRole('button',{name:'Download responses'}).click();
  const responsePath=join(directory,'test-response.json');
  await (await event).saveAs(responsePath);
  const result=JSON.parse(execFileSync('python3',['research/recognition_trial/analyze.py',join(directory,'key.json'),responsePath],{encoding:'utf8'}));
  assert.equal(result.participants,1);
  assert.equal(result.equalPairRecognitionDifference,null);
  assert.ok(result.pairs.every(pair=>(pair.schoolShown??pair.schoolHidden).abstentions===2));
  console.log('Phone-viewport volunteer workflow passed including optional blanks and downloaded response.');
} finally {
  await browser?.close();
  rmSync(directory,{recursive:true,force:true});
}
