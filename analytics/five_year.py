"""Empirical five-season participation trajectories, strict and retrospective.
Strict2018 uses only2013 cohort labels observed through2017. Missing2012 data
is not zero. This forecasts participation, not latent talent or causal wins.
"""
from pathlib import Path
import argparse,hashlib,json,math,time
import numpy as np
import pandas as pd
import train_models as tm
R=Path(__file__).resolve().parents[1];A=R/'analytics';RAW=R/'data/raw'
VERSION='five-year-participation-2018-donors-v1';CUTOFF='2018-04-26T00:00:00Z'

def group(p):return 'ST' if p in ['K','P','LS'] else ('LB' if p=='EDGE' else tm.pos_group(p))

def load_annual(start,end):
 games=pd.read_csv(RAW/'games.csv',low_memory=False);annual={};coverage={};name_lookup={}
 for year in range(start,end+1):
  f=RAW/f'snap_counts_{year}.csv'
  if not f.exists():raise ValueError(f'Missing source {f}')
  s=pd.read_csv(f)
  if s.empty:raise ValueError(f'{year} snap source is header-only, not observed zero outcomes')
  s=s[s.game_type=='REG'].copy();expected=set(games[(games.season==year)&(games.game_type=='REG')&games.home_score.notna()&games.away_score.notna()].game_id);found=set(s.game_id)
  if expected!=found:raise ValueError(f'Snap game coverage mismatch {year}: absent={sorted(expected-found)}, extra={sorted(found-expected)}')
  if s.duplicated(['game_id','pfr_player_id']).any():raise ValueError('Duplicate player-game records')
  s['scrimmage']=s.offense_snaps+s.defense_snaps;s['played']=(s.scrimmage+s.st_snaps)>0
  for pid,rows in s.groupby('pfr_player_id'):annual[(year,pid)]={'snaps':int(rows.scrimmage.sum()),'games':int(rows.loc[rows.played,'game_id'].nunique()),'specialSnaps':int(rows.st_snaps.sum())}
  ns=s[['player','pfr_player_id','position']].drop_duplicates();ns['broadPosition']=ns.position.map(group);ns['key']=ns.player.map(lambda v:''.join(c for c in str(v).lower() if c.isalpha()))
  for (key,position),rows in ns.groupby(['key','broadPosition']):
   if rows.pfr_player_id.nunique()==1:name_lookup[(year,key,position)]=rows.pfr_player_id.iloc[0]
  coverage[str(year)]={'expectedGames':len(expected),'observedGames':len(found),'rows':len(s),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 return annual,coverage,name_lookup

def build_cohorts(years,annual,names):
 c=pd.read_csv(RAW/'combine.csv',low_memory=False);c=c[c.season.isin(years)].copy();c['position']=c.pos.map(group);c['height']=c.ht.map(lambda v:float(str(v).split('-')[0])*12+float(str(v).split('-')[1]) if '-' in str(v) else np.nan);repairs=[]
 for ix,r in c[c.pfr_id.isna()].iterrows():
  key=''.join(x for x in str(r.player_name).lower() if x.isalpha());pid=names.get((r.season,key,r.position))
  if pid:c.loc[ix,'pfr_id']=pid;repairs.append({'cohort':int(r.season),'name':r.player_name,'pfrId':pid,'rule':'unique normalized-name plus broad-position match in rookie-season snap source'})
 excluded=c[c.pfr_id.isna()].groupby('season').size().to_dict();c=c[c.pfr_id.notna()].copy()
 if c.duplicated(['season','pfr_id']).any():raise ValueError('Duplicate cohort-player ID')
 for j in range(5):
  c[f'snaps{j+1}']=[annual.get((int(r.season)+j,r.pfr_id),{'snaps':0})['snaps'] for r in c.itertuples()]
  c[f'games{j+1}']=[annual.get((int(r.season)+j,r.pfr_id),{'games':0})['games'] for r in c.itertuples()]
 c['labelAvailableBy']=c.season.map(lambda y:f'{int(y)+5}-03-01');return c,excluded,repairs

def strict():
 annual,coverage,names=load_annual(2013,2017);d,excluded,repairs=build_cohorts([2013],annual,names);donors=[]
 for r in d.itertuples():
  snaps=[int(getattr(r,f'snaps{i}')) for i in range(1,6)];games=[int(getattr(r,f'games{i}')) for i in range(1,6)];donors.append({'position':r.position,'snaps':snaps,'games':games,'rookieRole':snaps[0]>=200})
 support={pos:{'donors':len(g),'rookieRole':int((g.snaps1>=200).sum()),'noRookieRole':int((g.snaps1<200).sum()),'roleConditioningSupported':bool(pos!='ST' and (g.snaps1>=200).any() and (g.snaps1<200).any())} for pos,g in d.groupby('position')}
 assert all(pd.Timestamp(v)<pd.Timestamp(CUTOFF) for v in pd.to_datetime(d.labelAvailableBy,utc=True));assert d.season.eq(2013).all()
 result={'version':VERSION,'cutoff':CUTOFF,'asOf':'2026-11-02','target':'Five annual regular-season scrimmage-snap counts and games with recorded snaps; not games started','cohorts':[2013],'labelSeasons':[2013,2017],'donors':donors,'supportByPosition':support,'validation':{'status':'fit-only; no independent pre2018 chronological test possible','chronologicallyValidatedFor2018':False,'n':len(d),'excludedUnknownIds':{str(k):int(v) for k,v in excluded.items()},'reason':'2012 snap source is header-only. Only2013 has all five annual outcomes observable before2018 draft.','samplingPolicy':'Condition within broad position on rookieRole using a pooled calibrated rookie-role probability if both strata exist; otherwise use position-wide donors. Draw one whole five-year vector.','specialists':'ST scrimmage snaps are not a specialist quality metric; do not condition on scrimmage role or infer specialist skill.','uncertainty':'Empirical donor variation is conditional on one cohort and observed opportunity; it does not include full parameter or model uncertainty.'},'sourceCoverage':coverage,'limitations':['Known-ID selection bias; unknown identities excluded.','No independent strict2018 chronological validation and only one donor cohort.','Actual opportunity, injuries, coaching and roster context are confounded in donor outcomes.','Games count positive recorded snaps, not official credited appearances or starts.','Future17-game seasons require an explicit exposure policy; no silent rescaling is empirically validated.','No causal mapping from snaps to team wins or value is identified.','Whole trajectory sampling preserves donor correlations but not causal context or unobserved talent.']}
 (A/'five_year_strict_2018.json').write_text(json.dumps(result,indent=2)+'\n');d[['season','pfr_id','position','labelAvailableBy']+[f'{kind}{i}' for kind in ['snaps','games'] for i in range(1,6)]].to_csv(A/'five_year_strict_labels.csv',index=False);(A/'five_year_identity_repairs.json').write_text(json.dumps(repairs,indent=2)+'\n');print(json.dumps({'strictDonors':len(d),'support':support,'excluded':excluded},indent=2));return result


SNAPS=[f'snaps{i}' for i in range(1,6)];GAMES=[f'games{i}' for i in range(1,6)]

def distribution_metrics(y,samples):
 pred=samples.mean(axis=1);total=y.sum(axis=1);pt=pred.sum(axis=1);st=samples.sum(axis=2)
 result={'n':len(y),'annualMAE':float(np.abs(y-pred).mean()),'annualRMSE':float(np.sqrt(((y-pred)**2).mean())),'totalMAE':float(np.abs(total-pt).mean()),'totalRMSE':float(np.sqrt(((total-pt)**2).mean())),'roleBrierByYear':list(map(float,np.mean(((samples>=200).mean(axis=1)-(y>=200))**2,axis=0))),'anyRoleBrier':float(np.mean((((samples>=200).any(axis=2)).mean(axis=1)-(y>=200).any(axis=1))**2))}
 for nominal in [.8,.95]:
  lo,hi=np.quantile(st,[(1-nominal)/2,1-(1-nominal)/2],axis=1);result[f'totalInterval{int(nominal*100)}']={'coverage':float(np.mean((total>=lo)&(total<=hi))),'meanWidth':float(np.mean(hi-lo))}
 return result

def role_predictions(train,test):
 # Hyperparameter C10 was selected with first-year labels available before2018.
 X=train[tm.FEATURES];y=(train.snaps1>=200).astype(int);model=tm.logistic(10.).fit(X,y);return model.predict_proba(test[tm.FEATURES])[:,1]

def donors_samples(train,test,probs=None,seed=20180426,n=400):
 rng=np.random.default_rng(seed);out=[]
 for i,r in enumerate(test.itertuples()):
  pool=train[train.position==r.position]
  if pool.empty:pool=train
  weights=np.ones(len(pool))/len(pool)
  if probs is not None:
   positive=(pool.snaps1>=200).to_numpy()
   if positive.any() and (~positive).any():weights=np.where(positive,probs[i]/positive.sum(),(1-probs[i])/(~positive).sum())
  idx=rng.choice(len(pool),size=n,replace=True,p=weights);out.append(pool[SNAPS].to_numpy()[idx])
 return np.asarray(out,dtype=float)

def ridge_fit(train,alpha):
 from sklearn.pipeline import Pipeline
 from sklearn.linear_model import Ridge
 model=Pipeline([('features',tm.prepare()),('regressor',Ridge(alpha=alpha))]).fit(train[tm.FEATURES],np.log1p(train[SNAPS].to_numpy()));residual=np.log1p(train[SNAPS].to_numpy())-model.predict(train[tm.FEATURES]);return model,residual

def ridge_samples(model,residual,test,seed=20180426,n=400):
 rng=np.random.default_rng(seed);pred=model.predict(test[tm.FEATURES]);idx=rng.integers(0,len(residual),size=(len(test),n));logdraw=pred[:,None,:]+residual[idx];return np.maximum(0,np.expm1(np.minimum(logdraw,20)))

def researched():
 end=2017
 for y in range(2018,2026):
  path=RAW/f'snap_counts_{y}.csv'
  if path.exists() and path.stat().st_size>1000:end=y
  else:break
 if end<2022:raise ValueError('Retrospective five-year testing requires complete2018–2022 snap files')
 annual,coverage,names=load_annual(2013,end);all_data,excluded,repairs=build_cohorts(list(range(2013,end-3)),annual,names);d=all_data[all_data.position!='ST'].copy();train=d[d.season.between(2013,2015)];val=d[d.season==2016];test=d[d.season.between(2017,2018)]
 assert len(train) and len(val) and len(test)
 vp=role_predictions(train,val);tp=role_predictions(train,test);experiments=[];candidates=[]
 for alpha in [1.,10.,100.,1000.]:
  model,residual=ridge_fit(train,alpha);sample=ridge_samples(model,residual,val);metric=distribution_metrics(val[SNAPS].to_numpy(),sample);experiments.append({'method':'log1p-ridge-residual-trajectories','alpha':alpha,'validation':metric});candidates.append((metric['totalRMSE'],alpha,model,residual))
 _,alpha,model,residual=min(candidates,key=lambda x:x[0]);outputs={'positionDonors':donors_samples(train,test),'roleConditionalDonors':donors_samples(train,test,tp),'log1pRidge':ridge_samples(model,residual,test)};metrics={name:distribution_metrics(test[SNAPS].to_numpy(),sample) for name,sample in outputs.items()}
 val_metrics={'positionDonors':distribution_metrics(val[SNAPS].to_numpy(),donors_samples(train,val)),'roleConditionalDonors':distribution_metrics(val[SNAPS].to_numpy(),donors_samples(train,val,vp)),'log1pRidge':distribution_metrics(val[SNAPS].to_numpy(),ridge_samples(model,residual,val))};selected=min(val_metrics,key=lambda name:val_metrics[name]['totalRMSE']);subgroups=[]
 for kind,col in [('cohort','season'),('position','position')]:
  for value,g in test.groupby(col):
   indices=test.index.get_indexer(g.index);subgroups.append({'group':kind,'value':value.item() if hasattr(value,'item') else value,'metrics':distribution_metrics(g[SNAPS].to_numpy(),outputs[selected][indices])})
 prediction=test[['season','pfr_id','position']+SNAPS+GAMES].copy()
 for name,sample in outputs.items():
  prediction[name+'_totalMean']=sample.sum(axis=2).mean(axis=1);prediction[name+'_totalP10']=np.quantile(sample.sum(axis=2),.1,axis=1);prediction[name+'_totalP90']=np.quantile(sample.sum(axis=2),.9,axis=1)
 prediction.to_csv(A/'five_year_retrospective_predictions.csv',index=False)
 correlation={'trainingObserved':np.corrcoef(train[SNAPS].to_numpy().T).tolist(),'heldoutObserved':np.corrcoef(test[SNAPS].to_numpy().T).tolist(),'selectedSimulated':np.corrcoef(outputs[selected].reshape(-1,5).T).tolist()}
 # Genuine label-available forecast-origin tests, separated from retrospective selection.
 # For yearY, donor cohorts <=Y-5 complete their five seasons by MarchY.
 rolling=[];rolling_predictions=[]
 # First-year training can include cohorts whose five-year outcomes are incomplete at cutoff;
 # only the first-year label is used in that role classifier.
 c=pd.read_csv(RAW/'combine.csv',low_memory=False);c=c[c.season.between(2013,end-4)].copy();c['position']=c.pos.map(group);c['height']=c.ht.map(lambda v:float(str(v).split('-')[0])*12+float(str(v).split('-')[1]) if '-' in str(v) else np.nan)
 for year in range(2018,min(2021,end-4)+1):
  donor=d[d.season<=year-5];target=d[d.season==year]
  if donor.empty or target.empty:continue
  assert pd.to_datetime(donor.labelAvailableBy,utc=True).max()<pd.Timestamp(f'{year}-04-01',tz='UTC')
  # Role classifier outcomes are rookie-only and all complete before yearY.
  first_cohorts=list(range(2013,year));first,_,_=build_cohorts(first_cohorts,annual,names);first=first[first.position!='ST']
  # build_cohorts constructs future columns too, but they NEVER enter this fit.
  assert first.season.max()<year
  probs=role_predictions(first,target)
  samples=donors_samples(donor,target,probs,seed=20180426+year)
  unconditional=donors_samples(donor,target,seed=20180426+year)
  row={'forecastDraftYear':year,'informationCutoff':f'{year}-04-01','donorCohorts':sorted(map(int,donor.season.unique())),'rookieClassifierCohorts':sorted(map(int,first.season.unique())),'nDonors':len(donor),'nTest':len(target),'metrics':distribution_metrics(target[SNAPS].to_numpy(),samples),'positionBaseline':distribution_metrics(target[SNAPS].to_numpy(),unconditional),'status':'frozen historical forecast evaluated later; no test-cohort labels used for fit'};rolling.append(row)
  for r,pred in zip(target.itertuples(),samples.sum(axis=2).mean(axis=1)):rolling_predictions.append({'year':year,'pfrId':r.pfr_id,'actualTotalSnaps':sum(getattr(r,k) for k in SNAPS),'predictedTotalSnaps':float(pred)})
 result={'version':'five-year-retrospective-and-rolling-v1','asOf':'2026-11-02','target':'Annual regular-season scrimmage snaps, not latent talent, starts, injury risk or causal wins','cohortSplit':{'train':[2013,2015],'validation':[2016,2016],'test':[2017,2018],'warning':'Retrospective cohort split: five-year training labels were not all available by2017 draft. This is NOT a strict2017 historical model.'},'counts':{'train':len(train),'validation':len(val),'test':len(test)},'selectedByValidationTotalRMSE':selected,'ridgeAlpha':alpha,'experiments':experiments,'validationMetrics':val_metrics,'testMetrics':metrics,'subgroupMetrics':subgroups,'trajectoryCorrelation':correlation,'rollingOriginTests':rolling,'sourceCoverage':coverage,'excludedUnknownIds':{str(k):int(v) for k,v in excluded.items()},'censoringPolicy':'Only cohorts with five fully covered observed regular seasons are included; missing recent follow-up is never zero.2012 excluded because source header-only. Known IDs absent from fully covered seasons receive zero observed snaps.','limitations':['Strict2018 production has only one complete donor cohort and cannot have an internal chronological validation split.','Rolling tests evaluate frozen historical forecasts later, without retroactively providing future labels to those forecasts.','Known-ID selection bias remains.','Residual bootstrap intervals are empirical approximations, not guaranteed conformal coverage.','Donor cohort correlations include historical team context and do not identify causal player ability.','No snaps-to-wins coefficient is estimated here.','Runtime profile pooling is evaluated separately; rolling first-year probabilities here are unpooled unless noted.','Specialists excluded from scrimmage-model benchmarks; their games-with-snaps donors remain available in strict artifact.']}

 def production_probabilities():
  raw=json.loads((A/'model.json').read_text());scenario=json.loads((R/'data/processed/scenario-2018.json').read_text());preds={p['prospectId']:p for p in raw['prospect']['projections']};buckets={};pooled={}
  for prospect in scenario['prospects']:
   if prospect.get('eligibilitySource')!='combine-participant':continue
   position=group(prospect['position']);p=preds[prospect['id']].get('roleProbability');p=float(raw['prospect']['globalPrior'] if p is None else p);buckets.setdefault(position,[]).append((p,prospect['id']))
  for values in buckets.values():
   values.sort();chunks=[values[i:i+5] for i in range(0,len(values),5)]
   if len(chunks)>1 and len(chunks[-1])<5:chunks[-2].extend(chunks.pop())
   for chunk in chunks:
    mean=sum(v[0] for v in chunk)/len(chunk)
    for _,pid in chunk:pooled[pid]=mean
  return pooled,raw['version']+'+blind-g5-v1'
 pooled,rookie_version=production_probabilities();target2018=d[d.season==2018].copy();donor2013=d[d.season==2013]
 import re
 norm=lambda x:re.sub('[^a-z0-9]','',str(x).lower())
 school=lambda x:norm(str(x).replace(' St.',' State').replace('Southern California','USC').replace('Louisiana-Lafayette','Louisiana'))
 ids=['p2018-'+hashlib.sha256((norm(r.player_name)+'|'+school(r.school)).encode()).hexdigest()[:10] for r in target2018.itertuples()]
 assert all(pid in pooled for pid in ids)
 p2018=np.asarray([pooled[pid] for pid in ids]);draws2018=donors_samples(donor2013,target2018,p2018,seed=20180426);base2018=donors_samples(donor2013,target2018,seed=20180426)
 frozen={'informationCutoff':CUTOFF,'cohorts':[2013],'labelSeasons':[2013,2017],'testDraftYear':2018,'testOutcomeSeasons':[2018,2022],'nDonors':len(donor2013),'nTest':len(target2018),'rookieModelVersion':rookie_version,'runtimePolicy':'Same broad-position and rookieRole conditional2013 donors; same frozen2018 shared-profile pooled rookie probabilities; forecasts are before cap/opportunity or snaps-to-wins transforms.','metrics':distribution_metrics(target2018[SNAPS].to_numpy(),draws2018),'positionBaseline':distribution_metrics(target2018[SNAPS].to_numpy(),base2018),'subgroups':[]}
 for position,g in target2018.groupby('position'):
  ix=target2018.index.get_indexer(g.index);frozen['subgroups'].append({'position':position,'metrics':distribution_metrics(g[SNAPS].to_numpy(),draws2018[ix])})
 fe=target2018[['season','pfr_id','position']+SNAPS+GAMES].copy();fe['prospectId']=ids;fe['pooledRookieProbability']=p2018;fe['predictedTotalSnaps']=draws2018.sum(axis=2).mean(axis=1);fe['baselineTotalSnaps']=base2018.sum(axis=2).mean(axis=1);fe['lower80']=np.quantile(draws2018.sum(axis=2),.1,axis=1);fe['upper80']=np.quantile(draws2018.sum(axis=2),.9,axis=1);fe.to_csv(A/'five_year_frozen_2018_predictions.csv',index=False)
 result['frozen2018ProductionModel']=frozen
 (A/'five_year_research.json').write_text(json.dumps(result,indent=2)+'\n');pd.DataFrame(rolling_predictions).to_csv(A/'five_year_rolling_predictions.csv',index=False)
 print(json.dumps({'counts':result['counts'],'selected':selected,'test':metrics,'rolling':rolling},indent=2));return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--strict-only',action='store_true');args=parser.parse_args();strict()
 if not args.strict_only:researched()
