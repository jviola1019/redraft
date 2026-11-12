"""Frozen pre-2018 forecasting experiment. Run from repository root.
No draft position, future career aggregates, player names or post-2017 outcomes
are permitted prediction features. Source availability is reconstructed, not archival.
"""
from pathlib import Path
import hashlib,json,math,platform,re,time
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.linear_model import LinearRegression,Ridge,LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss,log_loss,roc_auc_score,mean_absolute_error,mean_squared_error
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw';OUT=ROOT/'analytics'
SEED=20180426;CUTOFF='2018-04-26T00:00:00Z'
NUM=['height','wt','forty','bench','vertical','broad_jump','cone','shuttle'];FEATURES=NUM+['position']
BANDS={'height':3,'wt':15,'forty':.2,'bench':5,'vertical':5,'broad_jump':10,'cone':.2,'shuttle':.2}
def norm_team(t):return {'SD':'LAC','STL':'LAR','LA':'LAR','LV':'OAK','JAC':'JAX'}.get(t,t)
def pos_group(x):return {'CB':'DB','S':'DB','FS':'DB','SS':'DB','ILB':'LB','OLB':'LB','DE':'DL','DT':'DL','NT':'DL','OT':'OL','OG':'OL','G':'OL','C':'OL','T':'OL','FB':'RB'}.get(x,x)
def continuous(y,p):return {'n':len(y),'mae':float(mean_absolute_error(y,p)),'rmse':float(np.sqrt(mean_squared_error(y,p)))}
def binary(y,p,bootstrap=True):
 y=np.asarray(y);p=np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6)
 r={'n':len(y),'positiveRate':float(y.mean()),'brier':float(brier_score_loss(y,p)),'logLoss':float(log_loss(y,p,labels=[0,1])),'rocAuc':float(roc_auc_score(y,p)) if len(np.unique(y))>1 else None}
 if np.std(p)>1e-7 and len(np.unique(y))>1:
  c=LogisticRegression(C=1e6).fit(np.log(p/(1-p))[:,None],y);r.update(calibrationIntercept=float(c.intercept_[0]),calibrationSlope=float(c.coef_[0,0]))
 else:r.update(calibrationIntercept=None,calibrationSlope=None)
 r['reliability']=[]
 for lo in np.arange(0,1,.1):
  ix=(p>=lo)&(p<lo+.1)
  if ix.sum():r['reliability'].append({'from':round(float(lo),2),'to':round(float(lo+.1),2),'n':int(ix.sum()),'predicted':float(p[ix].mean()),'observed':float(y[ix].mean())})
 if bootstrap:
  rng=np.random.default_rng(SEED);b=[]
  for _ in range(500):
   ix=rng.integers(0,len(y),len(y));b.append(float(np.mean((p[ix]-y[ix])**2)))
  r['brierBootstrap95']=list(map(float,np.quantile(b,[.025,.975])))
 return r

def fit_teams():
 g=pd.read_csv(RAW/'games.csv',low_memory=False);g=g[(g.season<=2017)&(g.game_type=='REG')].dropna(subset=['home_score','away_score']).copy()
 for c in ['home_team','away_team']:g[c]=g[c].map(norm_team)
 rows=[]
 for r in g.itertuples():
  rows += [{'season':r.season,'team':r.home_team,'margin':r.home_score-r.away_score},{'season':r.season,'team':r.away_team,'margin':r.away_score-r.home_score}]
 ts=pd.DataFrame(rows).groupby(['season','team']).margin.mean().reset_index();lookup={(int(r.season),r.team):r.margin for r in ts.itertuples()};samples=[]
 for r in g.itertuples():
  h=lookup.get((r.season-1,r.home_team));a=lookup.get((r.season-1,r.away_team))
  if h is None or a is None:continue
  samples.append({'season':r.season,'home_team':r.home_team,'away_team':r.away_team,'strength_diff':h-a,'neutral':0 if r.location=='Neutral' else 1,'margin':r.home_score-r.away_score,'total':r.home_score+r.away_score})
 d=pd.DataFrame(samples);train=d[d.season<=2013];val=d[d.season.between(2014,2015)];test=d[d.season.between(2016,2017)];cols=['strength_diff','neutral']
 linear=LinearRegression(fit_intercept=False).fit(train[cols],train.margin)
 candidates=[]
 for alpha in [1,10,100,1000]:
  model=Ridge(alpha=alpha,fit_intercept=False).fit(train[cols],train.margin);candidates.append((continuous(val.margin,model.predict(val[cols]))['rmse'],alpha,model))
 loss,alpha,ridge=min(candidates,key=lambda x:x[0]);selected='linear' if continuous(val.margin,linear.predict(val[cols]))['rmse']<=loss else 'ridge';chosen=linear if selected=='linear' else ridge
 base=np.repeat(float(train.margin.mean()),len(test));pred=chosen.predict(test[cols]);metrics={'baseline':continuous(test.margin,base),'linear':continuous(test.margin,linear.predict(test[cols])),'ridge':continuous(test.margin,ridge.predict(test[cols]))}
 export=test.copy();export['prediction']=pred;export['baseline_prediction']=base;export.to_csv(OUT/'outcomes/team_test_predictions.csv',index=False)
 sd=float((train.margin-chosen.predict(train[cols])).std())
 final=(LinearRegression(fit_intercept=False) if selected=='linear' else Ridge(alpha=alpha,fit_intercept=False)).fit(d[cols],d.margin)
 residual=d.margin-final.predict(d[cols]);total_res=d.total-d.total.mean();pairs=[]
 for r in ts.itertuples():
  p=lookup.get((r.season-1,r.team))
  if p is not None:pairs.append([p,r.margin])
 pairs=np.asarray(pairs);dyn=LinearRegression().fit(pairs[:,0,None],pairs[:,1]);err=pairs[:,1]-dyn.predict(pairs[:,0,None])
 signed=[]
 for r,v in zip(d.itertuples(),residual):signed.extend([{'season':r.season,'team':r.home_team,'residual':v},{'season':r.season,'team':r.away_team,'residual':-v}])
 group=pd.DataFrame(signed).groupby(['season','team']).residual.agg(['mean','size']);group=group[group['size']>=14];n=float(1/np.mean(1/group['size']));gv=float(residual.var(ddof=2));mv=float(group['mean'].var(ddof=1));tv=float(max(0,min(gv*.49,(mv-gv/n)/(1-1/n))));iv=gv-2*tv
 team={'target':'regular-season score margin; historical unconditional total score','homeAdvantage':float(final.coef_[1]),'strengthCoefficient':float(final.coef_[0]),'meanTotal':float(d.total.mean()),'residualMarginSd':math.sqrt(gv),'residualTotalSd':float(total_res.std(ddof=1)),'residualCorrelation':float(np.corrcoef(residual,total_res)[0,1]),'seasonShockSd':math.sqrt(tv),'gameMarginSd':math.sqrt(iv),'persistence':float(dyn.coef_[0]),'persistenceIntercept':float(dyn.intercept_),'seasonInnovationSd':float(err.std(ddof=2)),'initialStrength':{r.team:round(float(r.margin),6) for r in ts[ts.season==2017].itertuples()},'fitThroughSeason':2017,'validation':{'train':[2000,2013],'validation':[2014,2015],'test':[2016,2017],'metrics':metrics,'selected':selected,'ridgeAlpha':alpha,'selectionCriterion':'validation RMSE, not test error','margin95IntervalCoverage':float(np.mean(np.abs(test.margin-pred)<=1.96*sd)),'margin95IntervalWidth':3.92*sd},'residualDecomposition':{'method':'method of moments; approximate independent opponent effects','teamSeasonRows':len(group),'harmonicGamesPerTeam':n,'varianceOfSignedTeamMeanResidual':mv,'marginalGameResidualVariance':gv,'teamSeasonShockVariance':tv,'independentGameVariance':iv},'simulationTransition':'Use previous realized mean scoring margin once through strengthCoefficient; add team-season shock and game noise. Update prior from simulated PF-PA per game; do not apply persistence again.','limitations':['Team-season shock decomposition assumes approximately independent opponent effects.','Stationary total-score distribution does not model future scoring shifts.','No player-to-wins causal effect is identified.']}
 assert len(team['initialStrength'])==32
 return team

def prepare():return ColumnTransformer([('numeric',Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler())]),NUM),('position',OneHotEncoder(handle_unknown='ignore',sparse_output=False),['position'])],sparse_threshold=0)
def logistic(C):return Pipeline([('preprocess',prepare()),('classifier',LogisticRegression(C=C,max_iter=2000,random_state=SEED))])
def band(d):
 d=d.copy()
 for k,w in BANDS.items():d[k]=np.floor(d[k]/w+.5)*w
 return d
def probband(p):return np.clip(np.floor(np.asarray(p)/.1)*.1+.05,.05,.95)
def paired(y,p,b,years):
 delta=(np.asarray(p)-np.asarray(y))**2-(np.asarray(b)-np.asarray(y))**2;years=np.asarray(years);groups=[np.flatnonzero(years==v) for v in np.unique(years)];rng=np.random.default_rng(SEED);v=[]
 for _ in range(1000):
  ix=np.concatenate([rng.choice(g,len(g),replace=True) for g in groups]);v.append(float(delta[ix].mean()))
 return {'brierDifference':float(delta.mean()),'withinCohortBootstrap95':list(map(float,np.quantile(v,[.025,.975]))),'resamples':1000,'note':'Conditional on two test cohorts; not between-era uncertainty.'}

def fit_prospects():
 c=pd.read_csv(RAW/'combine.csv',low_memory=False);c=c[c.season.between(2013,2018)].copy();c['position']=c.pos.map(pos_group);c['height']=c.ht.map(lambda x:float(str(x).split('-')[0])*12+float(str(x).split('-')[1]) if '-' in str(x) else np.nan)
 normalize=lambda x:re.sub('[^a-z]','',str(x).lower());outcomes={};names={};coverage={};repairs=[];games=pd.read_csv(RAW/'games.csv',low_memory=False)
 for year in range(2013,2018):
  s=pd.read_csv(RAW/f'snap_counts_{year}.csv');s=s[s.game_type=='REG'].copy();expected=set(games[(games.season==year)&(games.game_type=='REG')].game_id);found=set(s.game_id)
  assert expected==found,f'Incomplete snap coverage {year}';assert s.season.eq(year).all();assert not s.duplicated(['game_id','pfr_player_id']).any()
  s['snaps']=s.offense_snaps+s.defense_snaps
  for pid,num in s.groupby('pfr_player_id').snaps.sum().items():outcomes[(year,pid)]=float(num)
  ns=s[['player','pfr_player_id']].drop_duplicates();ns['key']=ns.player.map(normalize)
  for key,sub in ns.groupby('key'):
   if sub.pfr_player_id.nunique()==1:names[(year,key)]=sub.pfr_player_id.iloc[0]
  coverage[str(year)]={'gamesExpected':len(expected),'gamesObserved':len(found),'rows':len(s),'uniquePlayers':int(s.pfr_player_id.nunique())}
 for ix,r in c[c.season<2018].iterrows():
  if pd.isna(r.pfr_id):
   pid=names.get((r.season,normalize(r.player_name)))
   if pid:c.loc[ix,'pfr_id']=pid;repairs.append({'year':int(r.season),'player':r.player_name,'id':pid,'rule':'unique exact punctuation-normalized name in cohort-season snaps'})
 known=c[(c.season<2018)&c.pfr_id.notna()&~c.position.isin(['K','P','LS'])].copy();known['snaps']=[outcomes.get((r.season,r.pfr_id),0) for r in known.itertuples()];known['y']=(known.snaps>=200).astype(int)
 assert not {'draft_round','draft_ovr','draft_team','draft_year','y','snaps','player_name'}.intersection(FEATURES)
 train=known[known.season.between(2013,2014)];val=known[known.season==2015];test=known[known.season.between(2016,2017)];gp=float(train.y.mean());priors=((train.groupby('position').y.sum()+10*gp)/(train.groupby('position').y.count()+10)).to_dict();baseline=lambda d:d.position.map(priors).fillna(gp).to_numpy()
 experiments=[];candidates=[]
 for C in [.01,.1,1.,10.]:
  m=logistic(C).fit(train[FEATURES],train.y);loss=float(brier_score_loss(val.y,m.predict_proba(val[FEATURES])[:,1]));candidates.append((loss,C,m));experiments.append({'kind':'logistic','C':C,'validationBrier':loss})
 loss,C,raw=min(candidates,key=lambda x:x[0]);gb=Pipeline([('preprocess',prepare()),('classifier',HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=7,l2_regularization=10,learning_rate=.05,random_state=SEED))]).fit(train[FEATURES],train.y);gbloss=float(brier_score_loss(val.y,gb.predict_proba(val[FEATURES])[:,1]));bloss=float(brier_score_loss(val.y,baseline(val)));experiments.extend([{'kind':'hist-gradient-boosting','maxLeafNodes':7,'maxIter':100,'l2':10,'validationBrier':gbloss},{'kind':'position-baseline','validationBrier':bloss}]);_,selected,model=min([(bloss,'position-baseline',None),(loss,'logistic',raw),(gbloss,'hist-gradient-boosting',gb)],key=lambda x:x[0]);pred=baseline(test) if model is None else model.predict_proba(test[FEATURES])[:,1]
 metrics={'globalBaseline':binary(test.y,np.repeat(gp,len(test))),'positionBaseline':binary(test.y,baseline(test)),'logistic':binary(test.y,raw.predict_proba(test[FEATURES])[:,1]),'histGradientBoosting':binary(test.y,gb.predict_proba(test[FEATURES])[:,1])}
 f=known[['season','pfr_id']+FEATURES].copy();f['original_available_at']=None;f['availability_status']='historical event; original publication timestamp not archived';f.to_csv(OUT/'features/combine_model_features.csv',index=False)
 labels=known[['season','pfr_id','snaps','y']].copy();labels['label_available_by']=labels.season.map(lambda y:f'{y+1}-03-01');labels.to_csv(OUT/'outcomes/rookie_snap_labels.csv',index=False)
 ex=test[['season','pfr_id','position','y']].copy();ex['selected_probability']=pred;ex['position_probability']=baseline(test);ex['global_probability']=gp;ex['missing_measurements']=test[NUM].isna().sum(axis=1);ex.to_csv(OUT/'outcomes/prospect_test_predictions.csv',index=False)
 subgroups=[]
 for kind,column in [('position','position'),('year','season')]:
  for value,sub in test.groupby(column):
   ix=test.index.get_indexer(sub.index);subgroups.append({'group':kind,'value':value.item() if hasattr(value,'item') else value,**binary(sub.y,pred[ix])})
 for label,mask in [('complete',test[NUM].isna().sum(axis=1).eq(0)),('missing_one_or_more',test[NUM].isna().sum(axis=1).gt(0))]:
  sub=test[mask];subgroups.append({'group':'measurement_missingness','value':label,**binary(sub.y,pred[test.index.get_indexer(sub.index)])})
 # New comparison: candidate coarsening picked for design, tuned ONLY on 2015.
 bc=[]
 for cc in [.01,.1,1.,10.]:
  bm=logistic(cc).fit(band(train)[FEATURES],train.y);vl=float(brier_score_loss(val.y,bm.predict_proba(band(val)[FEATURES])[:,1]));bc.append((vl,cc,bm))
 _,bC,bmodel=min(bc,key=lambda x:x[0]);bp=bmodel.predict_proba(band(test)[FEATURES])[:,1];rp=raw.predict_proba(test[FEATURES])[:,1]
 variants={'raw_measurement_logistic':rp,'coarse_measurement_logistic':bp,'raw_with_10point_display_midpoint':probband(rp),'coarse_with_10point_display_midpoint':probband(bp)}
 coarsening={'asOf':'2026-11-02','purpose':'candidate display-information compression, not proof of anonymity','bandWidths':BANDS,'bandRule':'nearest fixed-width band center; missing remains missing','probabilityBandRule':'display ten-percentage-point ranges; midpoint evaluated as representative probability','rawLogisticC':C,'coarseLogisticC':bC,'train':[2013,2014],'validation':[2015,2015],'test':[2016,2017],'variants':{k:binary(test.y,p) for k,p in variants.items()},'comparisonsVsRaw':{k:paired(test.y,p,rp,test.season) for k,p in variants.items() if k!='raw_measurement_logistic'},'baselineComparison':paired(test.y,rp,baseline(test),test.season),'limitations':['Bands are candidate product choices, not proven optimal privacy thresholds.','Predictive similarity does not establish equal human decision quality or resistance to player recognition.','College was not a model predictor; this experiment does not evaluate hiding college on user outcomes.','Verified pre-draft college production is unavailable, so production-stat masking cannot be evaluated here.','Only identifiable combine participants and two test cohorts; selected-cohort bias and weak era generalization remain.','No claim of differential privacy or guaranteed anonymity.']}
 (OUT/'coarsening_comparison.json').write_text(json.dumps(coarsening,indent=2)+'\n');ex2=ex.copy()
 for k,p in variants.items():ex2[k]=p
 ex2.to_csv(OUT/'outcomes/coarsening_test_predictions.csv',index=False)
 finalgp=float(known.y.mean());finalpriors=((known.groupby('position').y.sum()+10*finalgp)/(known.groupby('position').y.count()+10)).to_dict();current=c[c.season==2018].copy()
 if model is not None:model.fit(known[FEATURES],known.y);fp=model.predict_proba(current[FEATURES])[:,1]
 else:fp=current.position.map(finalpriors).fillna(finalgp).to_numpy()
 projections=[]
 for r,p in zip(current.itertuples(),fp):
  ok=r.position not in ['K','P','LS'];projections.append({'pfrId':None if pd.isna(r.pfr_id) else r.pfr_id,'name':r.player_name,'school':r.school,'position':r.position,'roleProbability':round(float(p),6) if ok else None,'target':'at least 200 rookie regular-season offensive/defensive snaps','supported':ok,'missingMeasurements':int(pd.isna([getattr(r,x) for x in NUM]).sum()),'trainingCohorts':[2013,2017]})
 return {'target':'200+ rookie-season regular-season scrimmage snaps among identifiable combine participants, excluding specialists','targetIsStarterProbability':False,'selected':selected,'logisticC':C,'features':FEATURES,'trainCohorts':[2013,2014],'validationCohorts':[2015,2015],'testCohorts':[2016,2017],'finalFitCohorts':[2013,2017],'labelAvailableBy':CUTOFF,'metrics':metrics,'selectedTestMetrics':binary(test.y,pred),'subgroupTestMetrics':subgroups,'experiments':experiments,'projections':projections,'positionPriors':finalpriors,'globalPrior':finalgp,'snapCoverage':coverage,'trainingRows':len(known),'excludedUnknownIdentities':int(((c.season<2018)&c.pfr_id.isna()).sum()),'identityRepairs':repairs,'limitations':['Rookie participation measures opportunity and availability, not talent, starting probability or five-year quality.','Unknown identities excluded: selection bias limits all-prospect generalization.','No verified college production or historical injury features.','Downloaded historical measurements lack original publication snapshots.','Five-year development and causal draft effects are not validated by this model.']}

def attach_catalog(artifact):
 identity_path=ROOT/'data/clean/prospect_identity_2018.json';scenario_path=ROOT/'data/clean/scenario_2018.json'
 if not identity_path.exists() or not scenario_path.exists():return artifact
 identities=json.loads(identity_path.read_text());scenario=json.loads(scenario_path.read_text());ps=artifact['prospect']['projections'];by_id={p['pfrId']:p for p in ps if p['pfrId']};by_name={}
 for p in ps:by_name.setdefault(p['name'],[]).append(p)
 prospects={p['id']:p for p in scenario['prospects']};final=[]
 for identity in identities:
  candidate=by_id.get(identity.get('pfrId'));pid=identity['prospectId'];source=prospects[pid]
  if candidate is None:
   matches=by_name.get(identity.get('combineName'),[])
   if len(matches)==1:candidate=matches[0]
   elif len(matches)>1:candidate=next((p for p in matches if p['school']==source.get('college')),None)
  if candidate is not None:final.append({**candidate,'prospectId':pid,'pfrId':identity.get('pfrId') or candidate.get('pfrId'),'projectionSource':'combine model'})
  else:
   group=pos_group(source.get('position',''));ok=group not in ['K','P','LS'];prior=artifact['prospect']['positionPriors'].get(group,artifact['prospect']['globalPrior']);final.append({'prospectId':pid,'pfrId':identity.get('pfrId'),'name':identity.get('sourceRowName'),'position':group,'roleProbability':prior if ok else None,'target':artifact['prospect']['target'],'supported':ok,'projectionSource':'position baseline; no combine measurements','missingMeasurements':8})
 assert len(final)==len(identities) and len({p['prospectId'] for p in final})==len(final)
 artifact['prospect']['projections']=final;return artifact

def main():
 started=time.perf_counter()
 for x in ['features','outcomes']: (OUT/x).mkdir(parents=True,exist_ok=True)
 artifact={'version':'redraft-2018-model-v1','cutoff':CUTOFF,'seed':SEED,'createdFromDataAsOf':'2026-11-02','status':'research-alpha','team':fit_teams(),'prospect':fit_prospects()};artifact=attach_catalog(artifact)
 files=[RAW/'games.csv',RAW/'combine.csv']+list(RAW.glob('snap_counts_201[3-7].csv'));artifact['sourceHashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files};artifact['runtimeSeconds']=round(time.perf_counter()-started,3);artifact['environment']={'python':platform.python_version(),'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,'scikitLearn':__import__('sklearn').__version__}
 (OUT/'model.json').write_text(json.dumps(artifact,indent=2)+'\n');print(json.dumps({'selected':artifact['prospect']['selected'],'prospect':artifact['prospect']['selectedTestMetrics'],'team':artifact['team']['validation'],'runtimeSeconds':artifact['runtimeSeconds']},indent=2))
if __name__=='__main__':main()
