"""Research-only fixed-kernel historical joint-score donor experiment.

Protocol fixed before this execution: use prior ten completed seasons, Gaussian
kernel bandwidth six points on lagged-strength expected margin; do not tune.
Assess 2014-15 and 2016-17 separately, all already observed. Adoption requires
both windows to pass every gate below, plus a joint-season model validation that
this marginal donor experiment deliberately does not supply.
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import score_distribution as sd

SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else sd.ROOT/'data/raw/games.csv'
OUT=Path(__file__).with_name('empirical_score_pairs_results.json')
SEED=20261120
N=4096
PROTOCOL={
 'donorWindowSeasons':10,'marginKernelBandwidth':6,'minimumDonors':100,
 'evaluationWindows':[[2014,2015],[2016,2017]],
 'adoptionCriteria':{
  'totalMarginHomeAwayCRPS':'Each candidate mean CRPS <= baseline in EACH window',
  'totalMarginHomeAwayMAE':'Each candidate MAE <= 1.01 times baseline in EACH window',
  'shutoutBrier':'Candidate <= baseline in EACH window',
  'coverage':'For total, margin, home and away, absolute 90% coverage error <= baseline error + .01 in EACH window',
  'league':'Must validate a cutoff-safe shared team-season dependence model before adoption; marginal score-pair resampling cannot pass this gate'},
 'noTuningAfterAssessment':True,
 'status':'Retrospective fixed-design exploration; all assessment outcomes previously exposed'}

def load():
 g=pd.read_csv(SOURCE,low_memory=False)
 g=g[(g.game_type=='REG')&g.season.between(1999,2017)].dropna(subset=['home_score','away_score']).copy()
 for c in ['home_team','away_team']:g[c]=g[c].replace(sd.ALIASES)
 return sd.add_prior_context(g)

def donors(g,origin,law):
 d=g[g.season.between(origin-10,origin-1)].copy()
 assert d.season.max()<origin
 assert len(d)>=PROTOCOL['minimumDonors']
 return d,sd.expected_margin(d,law)

def draw_pairs(d,dm,mu,rng,n=N):
 w=np.exp(-.5*((dm-mu)/6)**2);w=w/w.sum()
 idx=rng.choice(len(d),size=n,p=w)
 return d.home_score.to_numpy()[idx],d.away_score.to_numpy()[idx],float(1/(w@w))

def metrics(h,a,row):
 out={}
 for key,x,y in [('total',h+a,row.total),('margin',h-a,row.margin),('home',h,row.home_score),('away',a,row.away_score)]:
  lo,hi=np.quantile(x,[.05,.95])
  out[key+'CRPS']=sd.crps(x,y);out[key+'MAE']=abs(float(x.mean())-y)
  out[key+'90']=float(lo<=y<=hi)
 p=float(np.mean((h==0)|(a==0)))
 out['shutoutBrier']=(p-float(row.shutout))**2
 out['predictedShutoutRate']=p
 return out

def assess(g,years):
 records={'normal':[],'empiricalPairs':[]};ess=[];fits=[]
 for year in years:
  law=sd.fit_score_law(g,year-1);d,dm=donors(g,year,law);fits.append({'testSeason':year,'fitThrough':year-1,'law':law,'donors':len(d)})
  for j,row in enumerate(g[g.season==year].itertuples()):
   rng=np.random.default_rng(np.random.SeedSequence([SEED,year,j]))
   h,a=sd.base_draw(row,law,rng,N)
   records['normal'].append(metrics(h,a,row))
   mu=law['homeAdvantage']+law['strengthCoefficient']*(row.home_prior-row.away_prior)
   h,a,e=draw_pairs(d,dm,mu,rng);ess.append(e)
   records['empiricalPairs'].append(metrics(h,a,row))
 summary={k:pd.DataFrame(v).mean().to_dict() for k,v in records.items()}
 b,c=summary['normal'],summary['empiricalPairs'];gates={}
 for key in ['total','margin','home','away']:
  gates[key+'CRPS']=c[key+'CRPS']<=b[key+'CRPS']
  gates[key+'MAE']=c[key+'MAE']<=1.01*b[key+'MAE']
  gates[key+'90Coverage']=abs(c[key+'90']-.9)<=abs(b[key+'90']-.9)+.01
 gates['shutoutBrier']=c['shutoutBrier']<=b['shutoutBrier']
 return {'years':years,'games':len(records['normal']),'fits':fits,'metrics':summary,'gates':gates,'allMarginalGatesPass':all(gates.values()),'effectiveDonorCount':{'min':min(ess),'median':float(np.median(ess))}}

def league(g,reps=1000):
 # Runtime-law comparator on a single known schedule, conditional on observed
 # preceding-season PF/PA. No player impacts, postseason or multi-year transition.
 year=2017;law=sd.fit_score_law(g,2016)
 # Runtime parameters through 2017 are not cutoff-safe for this 2017 illustration.
 # Instead decompose the pre-2017 fitted residual variance with pre-2017 residuals.
 tr=g[g.season.between(2000,2016)].copy();res=tr.margin.to_numpy()-sd.expected_margin(tr,law)
 signed=pd.DataFrame({'season':np.r_[tr.season,tr.season], 'team':np.r_[tr.home_team,tr.away_team], 'residual':np.r_[res,-res]})
 group=signed.groupby(['season','team']).residual.agg(['mean','size']);group=group[group['size']>=14]
 n=1/np.mean(1/group['size']);gv=np.var(res,ddof=2);mv=group['mean'].var(ddof=1)
 tv=max(0,min(gv*.49,(mv-gv/n)/(1-1/n)))
 d,dm=donors(g,year,law);schedule=g[g.season==year];teams=sorted(set(schedule.home_team)|set(schedule.away_team));ti={t:i for i,t in enumerate(teams)}
 rng=np.random.default_rng(SEED+1);shocks=rng.normal(0,np.sqrt(tv),(reps,len(teams)));wins={k:np.zeros((reps,len(teams))) for k in ['normalSharedShock','empiricalMarginalOnly']};points={k:np.zeros_like(v) for k,v in wins.items()}
 for row in schedule.itertuples():
  hi,ai=ti[row.home_team],ti[row.away_team]
  mu=law['homeAdvantage']+law['strengthCoefficient']*(row.home_prior-row.away_prior)
  z1,z2=rng.normal(size=(2,reps));m=mu+shocks[:,hi]-shocks[:,ai]+np.sqrt(gv-2*tv)*z1
  t=np.maximum(6,law['meanTotal']+law['totalSd']*(law['rho']*z1+np.sqrt(1-law['rho']**2)*z2))
  bh,ba=sd.nfl_scores(t,m,rng.random(reps),rng.random(reps))
  eh,ea,_=draw_pairs(d,dm,mu,rng,reps)
  for key,h,a in [('normalSharedShock',bh,ba),('empiricalMarginalOnly',eh,ea)]:
   wins[key][:,hi]+=(h>a)+.5*(h==a);wins[key][:,ai]+=(a>h)+.5*(h==a)
   points[key][:,hi]+=h;points[key][:,ai]+=a
 out={}
 for key,w in wins.items():
  out[key]={'meanWithinTeamWinSd':float(np.std(w,axis=0).mean()),'pooledWinQuantiles':np.quantile(w,[.05,.5,.95]).tolist(),'probabilityAnyTeamAtLeast14Wins':float(np.mean(w.max(axis=1)>=14)),'probabilityAnyTeamAtMost2Wins':float(np.mean(w.min(axis=1)<=2)),'meanWithinTeamSeasonPointsSd':float(np.std(points[key],axis=0).mean())}
 return {'season':year,'simulations':reps,'fitThrough':2016,'teamSeasonShockSd':float(np.sqrt(tv)),'metrics':out,'gatePass':False,'limit':'Donor draws preserve exact observed score pairs but independently resample each game, removing shared team-season shocks. This league check is descriptive, not a validation against observed seasons. No draft impacts, postseason, schedule regeneration or five-year path.'}

def main():
 g=load();results={'protocol':PROTOCOL,'sourceSha256':sd.sha(SOURCE),'assessments':[assess(g,y) for y in PROTOCOL['evaluationWindows']],'league':league(g)}
 results['adopt']=False
 results['decision']='Do not adopt. Report every predefined gate and joint-season limitation; score-pair support is empirical, not a generative NFL scoring mechanism.'
 OUT.write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__':main()
