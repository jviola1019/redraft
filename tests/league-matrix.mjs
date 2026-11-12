/** Finite structural audit. The seed matrix is fixed before inspecting outcomes. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {writeFileSync, mkdirSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import os from 'node:os';
import {engine, sim, loadScenario, cleanup, hashes} from '../analytics/runtime_loader.mjs';

const scenarioYear = Number(process.env.REDRAFT_SCENARIO_YEAR || 2018);
const { dataset, models } = loadScenario(scenarioYear);
const output = resolve(process.argv[2] || 'tests/results/league-matrix.json');
const seeds = ['redraft-structural-matrix-v1-a', 'redraft-structural-matrix-v1-b', 'redraft-structural-matrix-v1-c'];
const fixedTime = '2026-11-04T00:00:00Z';
const startedAt = new Date().toISOString(), started = performance.now(), sourceHashes = hashes();
const teams = dataset.teams.map(t => t.id).sort(), teamSet = new Set(teams);
const prospects = new Map(dataset.prospects.map(p => [p.id, p]));
const positions = {QB:1, RB:2, WR:3, TE:2, OL:5, DL:4, LB:3, DB:5, K:1, P:1, LS:1};
const rows = [], failures = [];
let assertions = 0, worlds = 0, seasons = 0, regularGames = 0, postseasonGames = 0, replayPairs = 0;
const check = (condition, message) => {assertions++; assert.ok(condition, message);};
const equal = (a, b, message) => {assertions++; assert.deepEqual(a, b, message);};
const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

function inspectDraft(game) {
  check(game.status === 'ready', 'Complete draft must be ready');
  equal(game.selections.length, dataset.picks.length, 'Every original slot is filled');
  equal(new Set(game.selections.map(p => p.prospectId)).size, game.selections.length, 'No duplicate players');
  equal(new Set(game.selections.map(p => p.overall)).size, game.selections.length, 'No duplicate slots');
  const owners = new Map(dataset.picks.map(p => [p.overall, p.owner]));
  for (const trade of game.trades) {
    check(trade.from !== trade.to && teamSet.has(trade.from) && teamSet.has(trade.to), 'Distinct valid trade parties');
    const assets = [...trade.give, ...trade.receive];
    equal(new Set(assets).size, assets.length, 'Trade assets cannot repeat');
    for (const [picks, from, to] of [[trade.give, trade.from, trade.to], [trade.receive, trade.to, trade.from]]) {
      for (const pick of picks) {
        check(pick >= trade.atPick, 'Already used assets cannot transfer');
        equal(owners.get(pick), from, 'Trade must own every asset');
        owners.set(pick, to);
      }
    }
  }
  for (const pick of game.picks) equal(pick.owner, owners.get(pick.overall), 'Final ownership reconciles to transactions');
  for (const pick of game.selections) {
    const prospect = prospects.get(pick.prospectId), slot = dataset.picks.find(p => p.overall === pick.overall);
    check(Boolean(prospect && engine.isPlayableProspect(prospect)), 'Only supported prospects are playable');
    check(new Date(prospect.availableBy).getTime() <= new Date(game.cutoff).getTime(), 'Selection cannot use post-cutoff prospect');
    equal(pick.round, slot.round, 'Round is historical slot round');
    equal(pick.team, owners.get(pick.overall), 'Selected team owns pick');
  }
  equal(engine.validateGame(game, dataset), true, 'Production validation also accepts draft');
}

function inspectWorld(world, team, allocations, label) {
  worlds++;
  equal(world.seasons.map(s => s.year), Array.from({length:5}, (_,i)=>scenarioYear+i), `${label}: five chronological seasons`);
  let totalWins = 0, appearances = 0, titles = 0;
  const expectedPlayers = new Map(allocations.map(s => [s.prospectId, s.team]));
  for (const season of world.seasons) {
    seasons++;
    const n = season.year < 2021 ? 16 : 17;
    const regular = season.games.filter(g => g.type === 'REG'), post = season.games.filter(g => g.type !== 'REG');
    regularGames += regular.length; postseasonGames += post.length;
    equal(regular.length, 32 * n / 2, 'Correct regular-season game count');
    equal(post.length, season.year < 2020 ? 11 : 13, 'Correct playoff game count');
    equal(new Set(season.games.map(g => g.id)).size, season.games.length, 'Game IDs are unique');
    equal([...season.teams.map(t => t.team)].sort(), teams, 'Exactly the supported 32 teams');
    const stats = new Map(teams.map(t => [t, {wins:0, losses:0, ties:0, pointsFor:0, pointsAgainst:0}]));
    for (const game of season.games) {
      check(teamSet.has(game.home) && teamSet.has(game.away) && game.home !== game.away, 'Game teams are valid and distinct');
      check(game.season === season.year && Number.isInteger(game.week) && game.week > 0, 'Game calendar is valid');
      for (const score of [game.homeScore, game.awayScore]) check(Number.isInteger(score) && score >= 0, 'Scores are nonnegative integers');
      if (game.type !== 'REG') {check(game.homeScore !== game.awayScore, 'Playoff games cannot tie'); continue;}
      const h = stats.get(game.home), a = stats.get(game.away);
      h.pointsFor += game.homeScore; h.pointsAgainst += game.awayScore;
      a.pointsFor += game.awayScore; a.pointsAgainst += game.homeScore;
      if (game.homeScore > game.awayScore) {h.wins++; a.losses++;}
      else if (game.homeScore < game.awayScore) {a.wins++; h.losses++;}
      else {h.ties++; a.ties++;}
    }
    for (const t of season.teams) {
      const actual = {wins:t.wins, losses:t.losses, ties:t.ties, pointsFor:t.pointsFor, pointsAgainst:t.pointsAgainst};
      equal(actual, stats.get(t.team), 'Record and points must come from games');
      const own = regular.filter(g => g.home === t.team || g.away === t.team);
      equal(own.length, n, 'Every team plays season game limit');
      equal(new Set(own.map(g => g.week)).size, n, 'No team plays twice in a week');
      const identity = dataset.teams.find(x => x.id === t.team);
      for (const rival of dataset.teams.filter(x => x.id !== t.team && x.division === identity.division && x.conference === identity.conference)) {
        const meetings = own.filter(g => g.home === rival.id || g.away === rival.id);
        equal(meetings.length, 2, 'Division opponents play twice');
        equal(meetings.filter(g => g.home === t.team).length, 1, 'Division opponents split home venues');
      }
      check(t.playoff === (t.seed !== null), 'Playoff flag matches seed availability');
      if (t.team === team) {totalWins += t.wins; appearances += Number(t.playoff); titles += Number(t.champion);}
    }
    equal(season.teams.reduce((s,t)=>s+t.wins,0), season.teams.reduce((s,t)=>s+t.losses,0), 'League wins equal losses');
    equal(season.teams.reduce((s,t)=>s+t.ties,0), regular.filter(g=>g.homeScore===g.awayScore).length*2, 'Tie entries reconcile');
    equal(season.teams.filter(t=>t.champion).map(t=>t.team), [season.champion], 'Exactly one recorded champion');
    equal(season.teams.filter(t=>t.conferenceChampion).length, 2, 'Exactly two conference champions');
    for (const conference of ['AFC','NFC']) {
      const participants = season.teams.filter(t=>dataset.teams.find(x=>x.id===t.team).conference===conference && t.playoff);
      equal(participants.map(t=>t.seed).sort((a,b)=>a-b), Array.from({length:season.year<2020?6:7},(_,i)=>i+1), 'Conference seeds complete and unique');
      const divisionWinners = participants.filter(t=>t.seed<=4).map(t=>dataset.teams.find(x=>x.id===t.team).division);
      equal(new Set(divisionWinners).size, 4, 'Top four seeds represent four divisions');
      const seedsByTeam = new Map(participants.map(t => [t.team, t.seed]));
      const winner = game => game.homeScore > game.awayScore ? game.home : game.away;
      const round = type => post.filter(g => g.type === type && seedsByTeam.has(g.home));
      const firstHost = season.year < 2020 ? 3 : 2;
      const wildcards = round('WC');
      const pairs = wildcards.map(g => [seedsByTeam.get(g.home), seedsByTeam.get(g.away)]);
      pairs.sort((a,b) => a[0] - b[0]);
      equal(pairs, Array.from({length:5-firstHost}, (_,i) => [firstHost+i, season.year<2020?6-i:7-i]), 'Wild card pairings follow era rules');
      const remaining = [...wildcards.map(winner), ...participants.filter(t => t.seed < firstHost).map(t => t.team)];
      remaining.sort((a,b) => seedsByTeam.get(a) - seedsByTeam.get(b));
      const divisional = round('DIV');
      equal(divisional.map(g => [g.home,g.away]), [[remaining[0],remaining[3]],[remaining[1],remaining[2]]], 'Divisional round reseeds after wild cards');
      const finalists = divisional.map(winner).sort((a,b) => seedsByTeam.get(a) - seedsByTeam.get(b));
      const title = round('CON');
      equal(title.map(g => [g.home,g.away]), [finalists], 'Higher remaining seed hosts conference championship');
      equal(participants.filter(t => t.conferenceChampion).map(t => t.team), title.map(winner), 'Conference champion won conference title game');

    }
    const bowl = post.filter(g=>g.type==='SB'); equal(bowl.length,1,'Exactly one Super Bowl');
    equal(bowl[0].homeScore > bowl[0].awayScore ? bowl[0].home : bowl[0].away, season.champion, 'Champion won the Super Bowl');
    equal(new Set(season.players.map(p=>p.prospectId)).size, allocations.length, 'Each drafted player appears exactly once per season');
    equal(season.players.length, allocations.length, 'Cohort player count conserved');
    const starts = new Map();
    for (const p of season.players) {
      equal(expectedPlayers.get(p.prospectId), p.team, 'Player remains on modeled cohort team');
      equal(p.season,season.year,'Player season matches league season');
      check(Number.isInteger(p.games)&&p.games>=0&&p.games<=n,'Player availability bounds');
      check(Number.isInteger(p.starts)&&p.starts>=0&&p.starts<=p.games,'Starts cannot exceed games');
      check(Number.isFinite(p.contribution)&&p.contribution>=0,'Contribution is finite and nonnegative');
      const group=engine.positionGroup(prospects.get(p.prospectId).position),key=`${p.team}:${group}`;
      starts.set(key,(starts.get(key)||0)+p.starts);
    }
    for (const [key,total] of starts) check(total <= (positions[key.split(':')[1]]||1)*n,'Position starts cannot exceed team opportunity');
    for (const star of season.starPicks) check(season.players.some(p=>p.prospectId===star.prospectId&&p.team===star.team),'Star pick comes from simulated cohort');
    for (const award of season.awards) check(award.prospectId===null||season.players.some(p=>p.prospectId===award.prospectId&&p.team===award.team),'Award winner comes from modeled cohort');
  }
  equal({totalWins,appearances,titles},{totalWins:world.totalWins,appearances:world.playoffAppearances,titles:world.titles},'Five-year headline reconciles to seasons');
}

try {
  equal(teams.length,32,'Matrix requires all 32 supported teams');
  for (const team of teams) {
    for (let seedIndex=0;seedIndex<seeds.length;seedIndex++) {
      const seed=seeds[seedIndex],begin=performance.now(),row={team,seed,status:'passed',replicates:[],replay:false};
      try {
        const config={id:`matrix-${team}-${seedIndex}`,team,seed,now:fixedTime,modelVersion:models.version};
        const game=engine.autoComplete(engine.createGame(config,dataset),dataset,models);
        inspectDraft(game); row.trades=game.trades.length; row.draftHash=digest(game);
        for(let index=0;index<2;index++) {
          const result=sim.simulateReplicate(game,index,dataset,models);
          inspectWorld(result.baseline,team,dataset.actualPicks,'historical baseline');
          inspectWorld(result.alternate,team,game.selections,'alternate');
          row.replicates.push({index,hash:digest(result),worldHash:digest({baseline:result.baseline,alternate:result.alternate}),baselineWins:result.baseline.totalWins,alternateWins:result.alternate.totalWins});
          if(seedIndex===0&&index===0) {
            const replayDraft=engine.autoComplete(engine.createGame(config,dataset),dataset,models);
            equal(replayDraft,game,'Same input config reproduces complete draft');
            equal(sim.simulateReplicate(replayDraft,index,dataset,models),result,'Same input config reproduces complete paired worlds');
            row.replay=true; replayPairs++;
          }
        }
        check(row.replicates[0].worldHash!==row.replicates[1].worldHash,'Independent replicate indices generate different worlds');
      } catch(error) {row.status='failed';row.error=error.stack||String(error);failures.push({team,seed,error:row.error});}
      row.durationMs=performance.now()-begin; rows.push(row);
    }
    console.log(`MATRIX ${team}: ${rows.filter(r=>r.team===team&&r.status==='passed').length}/3 cases passed`);
  }
} catch(error) {failures.push({error:error.stack||String(error)});}
finally {
  const finalHashes=hashes(),sourceChanged=Object.keys(sourceHashes).some(p=>sourceHashes[p]!==finalHashes[p]);
  if(sourceChanged) failures.push({error:'Runtime source/artifact changed during matrix execution'});
  const report={version:'league-structural-matrix-v1',startedAt,finishedAt:new Date().toISOString(),durationMs:performance.now()-started,configuration:{scenarioYear,teams,seeds,fixedGameTime:fixedTime,pairedReplicatesPerCase:2,replay:'First seed and replicate for every team',modelVersion:models.version,engineVersion:engine.RULE_VERSION,datasetVersion:dataset.metadata.version},planned:{draftCases:96,pairedReplicates:192,deterministicDraftAndPairReplays:32},actual:{draftCases:rows.length,passedCases:rows.filter(r=>r.status==='passed').length,failedCases:rows.filter(r=>r.status==='failed').length,pairedReplicates:rows.reduce((n,r)=>n+r.replicates.length,0),replayPairs,assertions,worlds,seasons,regularGames,postseasonGames},runtime:{node:process.version,platform:os.platform(),architecture:os.arch(),cpu:os.cpus()[0]?.model,logicalCpus:os.cpus().length},sourceHashes,finalHashes,sourceChanged,rows,failures,status:failures.length?'failed':'passed',limitations:['Finite prespecified seed coverage is not exhaustive verification.','Autocompleted drafts exercise one CPU policy; adversarial user trades are covered separately by domain/API tests.','Structural consistency does not establish forecast calibration, causal validity, exact NFL tiebreakers or complete historical rosters.','Monte Carlo replicate indices are fixed; failures are retained and never resampled.']};
  mkdirSync(dirname(output),{recursive:true});writeFileSync(output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});cleanup();
  console.log('LEAGUE_MATRIX_REPORT',JSON.stringify({status:report.status,...report.actual,durationMs:Math.round(report.durationMs),report:output}));
  if(failures.length)process.exitCode=1;
}
