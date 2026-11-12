"""Reproducible factual extraction. Actual results never become prospect predictors."""
from pathlib import Path
import csv,json,re,hashlib,collections,datetime,io
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw';OUT=ROOT/'data/clean';PROCESSED=ROOT/'data/processed'
SOURCE_COMBINE='https://github.com/nflverse/nflverse-data/releases/tag/combine'
SOURCE_DRAFT='https://github.com/nflverse/nflverse-data/releases/tag/draft_picks'
ORDER_URL='https://www.nfl.com/news/2018-nfl-draft-order-for-all-seven-rounds-0ap3000000919673'
TEAMS=[('ARI','Arizona Cardinals','NFC','West'),('ATL','Atlanta Falcons','NFC','South'),('BAL','Baltimore Ravens','AFC','North'),('BUF','Buffalo Bills','AFC','East'),('CAR','Carolina Panthers','NFC','South'),('CHI','Chicago Bears','NFC','North'),('CIN','Cincinnati Bengals','AFC','North'),('CLE','Cleveland Browns','AFC','North'),('DAL','Dallas Cowboys','NFC','East'),('DEN','Denver Broncos','AFC','West'),('DET','Detroit Lions','NFC','North'),('GB','Green Bay Packers','NFC','North'),('HOU','Houston Texans','AFC','South'),('IND','Indianapolis Colts','AFC','South'),('JAX','Jacksonville Jaguars','AFC','South'),('KC','Kansas City Chiefs','AFC','West'),('LAC','Los Angeles Chargers','AFC','West'),('LAR','Los Angeles Rams','NFC','West'),('MIA','Miami Dolphins','AFC','East'),('MIN','Minnesota Vikings','NFC','North'),('NE','New England Patriots','AFC','East'),('NO','New Orleans Saints','NFC','South'),('NYG','New York Giants','NFC','East'),('NYJ','New York Jets','AFC','East'),('OAK','Oakland Raiders','AFC','West'),('PHI','Philadelphia Eagles','NFC','East'),('PIT','Pittsburgh Steelers','AFC','North'),('SEA','Seattle Seahawks','NFC','West'),('SF','San Francisco 49ers','NFC','West'),('TB','Tampa Bay Buccaneers','NFC','South'),('TEN','Tennessee Titans','AFC','South'),('WAS','Washington Redskins','NFC','East')]
ALIASES={'GNB':'GB','KAN':'KC','NWE':'NE','NOR':'NO','SFO':'SF','TAM':'TB','SD':'LAC','SDG':'LAC','STL':'LAR','LA':'LAR','RAM':'LAR','RAI':'OAK','LVR':'OAK','LV':'OAK','JAC':'JAX','WSH':'WAS'}
def tid(s):return ALIASES.get(s,s)
REQUIRED_COLUMNS={
 'combine.csv':{'season','player_name','pos','school','pfr_id','ht','wt','forty','bench','vertical','broad_jump','cone','shuttle'},
 'draft_picks.csv':{'season','round','pick','team','pfr_player_id','pfr_player_name','position','college'},
 'games.csv':{'game_id','season','game_type','week','gameday','home_team','away_team','home_score','away_score'},
}
def rows(name):
 reader=csv.DictReader(io.StringIO((RAW/name).read_text()))
 missing=REQUIRED_COLUMNS.get(name,set())-set(reader.fieldnames or [])
 if missing:raise ValueError(f'{name}: missing required columns {sorted(missing)}')
 return list(reader)
def num(v):return float(v) if v and v not in ('NA','NaN') else None
def norm(s):return re.sub(r'[^a-z0-9]','',s.lower())
def college(s):return norm(s.replace(' St.',' State').replace('Southern California','USC').replace('Louisiana-Lafayette','Louisiana'))
def pid(name,school):return 'p2018-'+hashlib.sha256((norm(name)+'|'+college(school)).encode()).hexdigest()[:10]
def height(s):
 if not s:return None
 f,i=s.split('-');return int(f)*12+int(i)
def position(s):return {'OG':'G','OT':'T','ILB':'LB','OLB':'LB','DB':'CB','NT':'DT','FB':'RB'}.get(s,s)
def main():
 OUT.mkdir(exist_ok=True,parents=True);PROCESSED.mkdir(exist_ok=True,parents=True)
 allcombine=rows('combine.csv');drafts=rows('draft_picks.csv');allgames=rows('games.csv');combine=[r for r in allcombine if r['season']=='2018'];actual=[r for r in drafts if r['season']=='2018']
 bypfr={r['pfr_player_id']:r for r in actual if r['pfr_player_id']};byname=collections.defaultdict(list)
 for r in actual:byname[norm(r['pfr_player_name'])].append(r)
 manual={'foleyfatukasi':'Folorunso Fatukasi','treywalker':'Tracy Walker'};prospects=[];identities=[];resolved={};audit=[]
 for c in sorted(combine,key=lambda x:norm(x['player_name'])):
  match=bypfr.get(c['pfr_id']);rule='exact_pfr_id' if match else None
  if not match:
   candidates=byname.get(norm(c['player_name']),[])
   if len(candidates)==1 and college(c['school'])==college(candidates[0]['college']):match=candidates[0];rule='exact_normalized_name_and_college'
  if not match and norm(c['player_name']) in manual:
   candidates=byname[norm(manual[norm(c['player_name'])])]
   if len(candidates)==1 and college(c['school'])==college(candidates[0]['college']):match=candidates[0];rule='audited_alias_and_college'
  ident=pid(c['player_name'],c['school']);name=('Darius Leonard' if c['player_name']=='Darius Leonard' else match['pfr_player_name']) if match else c['player_name']
  item={'id':ident,'name':name,'position':position(c['pos']),'college':c['school'],'heightIn':height(c['ht']),'weightLb':num(c['wt']),'forty':num(c['forty']),'bench':num(c['bench']),'verticalIn':num(c['vertical']),'broadJumpIn':num(c['broad_jump']),'cone':num(c['cone']),'shuttle':num(c['shuttle']),'source':SOURCE_COMBINE,'availableBy':'2018-03-06','availabilityBasis':'Combine ended2018-03-05; original publication timestamp unavailable; reconstructed observations','eligibilitySource':'combine-participant','playable':True}
  prospects.append(item);identities.append({'prospectId':ident,'combineName':c['player_name'],'pfrId':match['pfr_player_id'] if match else c['pfr_id'] or None,'sourceRowName':c['player_name'],'matchRule':rule or 'unmatched-combine'})
  if match:
   assert match['pfr_player_id'] not in resolved
   resolved[match['pfr_player_id']]=ident;audit.append({'combineName':c['player_name'],'draftName':match['pfr_player_name'],'rule':rule,'verification':'exact identifier' if rule=='exact_pfr_id' else 'audited school-constrained identity rule','probabilisticConfidence':None})
 for d in actual:
  if d['pfr_player_id'] in resolved:continue
  ident=pid(d['pfr_player_name'],d['college']);assert ident not in {x['id'] for x in prospects}
  prospects.append({'id':ident,'name':d['pfr_player_name'],'position':position(d['position']),'college':d['college'] or 'Not applicable / not reported','heightIn':None,'weightLb':None,'forty':None,'bench':None,'verticalIn':None,'broadJumpIn':None,'cone':None,'shuttle':None,'source':SOURCE_DRAFT,'availableBy':'2018-04-26','availabilityBasis':'Retrospective identity; original eligibility/position publication not established; actual-history reference only','eligibilitySource':'retrospective-draft-record','playable':False})
  resolved[d['pfr_player_id']]=ident;identities.append({'prospectId':ident,'combineName':None,'pfrId':d['pfr_player_id'],'sourceRowName':d['pfr_player_name'],'matchRule':'retrospective_reference_only'})
 html=(RAW/'order_2018.html').read_text();article=json.loads(re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',html,re.S)[0]);body=article['articleBody'].replace('\\n','\n').replace('\\r','\r');names={name:code for code,name,_,_ in TEAMS};names['Tennesse Titans']='TEN';picks=[]
 for rnd,sec in enumerate(re.split(r'Round [1-7]',body)[1:],1):
  lines=[x.strip() for x in sec.splitlines() if x.strip() and not x.startswith('Pick')]
  for i,line in enumerate(lines,1):
   if rnd==1:overall=i;text=line
   else:
    m=re.match(r'(\d+) \((\d+)\)\. (.+)',line);assert m,line;assert int(m[1])==i;overall=int(m[2]);text=m[3]
   team=text.split(' from ')[0].replace(' (Compensatory)','');assert team in names,team;picks.append({'overall':overall,'round':rnd,'owner':names[team],'compensatory':'Compensatory' in text})
 assert [x['overall'] for x in picks]==list(range(1,257));assert sum(x['compensatory'] for x in picks)==32
 games=[{'id':r['game_id'],'season':int(r['season']),'type':r['game_type'],'week':int(r['week']),'date':r['gameday'],'home':tid(r['home_team']),'away':tid(r['away_team']),'homeScore':int(r['home_score']),'awayScore':int(r['away_score'])} for r in allgames if 2017<=int(r['season'])<=2022 and r['home_score'] and r['away_score']];teams=[]
 for code,name,conf,div in TEAMS:
  played=[g for g in games if g['season']==2017 and g['type']=='REG' and code in (g['home'],g['away'])];wins=losses=ties=pf=pa=0
  for g in played:
   own=g['homeScore'] if g['home']==code else g['awayScore'];opp=g['awayScore'] if g['home']==code else g['homeScore'];pf+=own;pa+=opp;wins+=own>opp;losses+=own<opp;ties+=own==opp
  assert len(played)==16;teams.append({'id':code,'name':name,'conference':conf,'division':div,'priorWins':wins,'priorLosses':losses,'priorTies':ties,'priorPointsFor':pf,'priorPointsAgainst':pa})
 actualp=[{'overall':int(d['pick']),'round':int(d['round']),'team':tid(d['team']),'prospectId':resolved[d['pfr_player_id']]} for d in actual]
 assert len({x['id'] for x in prospects})==len(prospects);assert len({x['prospectId'] for x in actualp})==256;assert all(x['team'] in {t['id'] for t in teams} for x in actualp)
 supplement=sum(not p['playable'] for p in prospects);verified=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
 metadata={'version':'nflverse-2018-combine-only-v2','draftYear':2018,'informationCutoff':'2018-04-26T23:59:00Z','verifiedDate':verified,'informationCutoffConfidence':'reconstructed-not-fully-archival','playableProspectCount':len(combine),'referenceOnlyProspectCount':supplement,'poolWarning':f'Playable pool restricted to{len(combine)} combine participants. {supplement} non-combine draftees appear only in actual-history/baseline references. Missing non-combine eligible players limit historical completeness. Research alpha; no fully reconstructed eligible population.','missingFields':['college-season production','pre-draft injury history','complete pre-draft rosters','contracts and cap','contemporaneous scouting grades'],'orderSource':ORDER_URL,'orderPublished':article['datePublished'],'orderModified':article['dateModified'],'orderWarning':'Current NFL article was modified after cutoff. Independently audited transaction reconstruction supports ownership; original publication timestamps remain incomplete.','attribution':'NFL factual order; nflverse and original providers Pro Football Reference(draft/combine) and Lee Sharpe(games). Published nflverse releases CC BY4.0. Normalized by REDRAFT; no official logos or photos used.','license':'https://creativecommons.org/licenses/by/4.0/'}
 dataset={'metadata':metadata,'teams':teams,'prospects':prospects,'picks':picks,'actualPicks':actualp,'games':games};text=json.dumps(dataset,separators=(',',':'))
 (OUT/'scenario_2018.json').write_text(text);(PROCESSED/'scenario-2018.json').write_text(text);(OUT/'prospect_identity_2018.json').write_text(json.dumps(identities,indent=2));(OUT/'entity_resolution.json').write_text(json.dumps(audit,indent=2))
 report={'datasetVersion':metadata['version'],'verifiedDate':verified,'teams':len(teams),'combineProspects':len(combine),'canonicalProspects':len(prospects),'referenceOnlyProspects':supplement,'draftPicks':len(picks),'compensatoryPicks':sum(x['compensatory'] for x in picks),'roundCounts':dict(collections.Counter(x['round'] for x in picks)),'games':len(games),'gamesBySeason':dict(collections.Counter(x['season'] for x in games)),'missingPlayableMeasurements':{f:sum(p[f] is None for p in prospects if p['playable']) for f in ['heightIn','weightLb','forty','bench','verticalIn','broadJumpIn','cone','shuttle']},'duplicateProspectIds':0,'duplicateActualSelections':0,'entityResolution':dict(collections.Counter(x['rule'] for x in audit)),'warnings':[metadata['poolWarning'],metadata['orderWarning'],'Annual2017 roster is not an April2018 roster snapshot.'],'checksPassed':['256 sequential picks','32 compensatory picks','seven true round lengths','32 teams','all2017 teams16 games','unique prospectIDs','unique actual selections','actual foreign keys resolved']};(OUT/'quality_report.json').write_text(json.dumps(report,indent=2))
 coverage=[]
 for year in range(2013,2022):
  cs=[x for x in allcombine if x['season']==str(year)];ds=[x for x in drafts if x['season']==str(year)];gs=[x for x in allgames if x['season']==str(year) and x['game_type']=='REG'];coverage.append({'year':year,'combineRows':len(cs),'draftSelections':len(ds),'regularSeasonGames':len(gs),'fortyMissing':sum(not x['forty'] for x in cs),'predraftOrderReconstructed':year==2018,'collegeProduction':False,'injuriesPredraft':False,'strictPublicationTimes':False,'releaseQualified':False})
 (OUT/'coverage_matrix.json').write_text(json.dumps(coverage,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
