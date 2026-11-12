"""Evaluate the shared-profile probability transformation on held-out cohorts.
Groups are built from ALL available same-year combine candidates before labels join.
Outcome labels never enter grouping. This measures predictive utility, not anonymity.
"""
from pathlib import Path
import json,hashlib,re
import numpy as np
import pandas as pd
import train_models as tm
R=Path(__file__).resolve().parents[1];A=R/'analytics';m=json.loads((A/'model.json').read_text())
f=pd.read_csv(A/'features/combine_model_features.csv');labels=pd.read_csv(A/'outcomes/rookie_snap_labels.csv');train=f.merge(labels[['season','pfr_id','y']],on=['season','pfr_id'],validate='one_to_one');train=train[train.season.between(2013,2014)]
model=tm.logistic(m['prospect']['logisticC']).fit(train[tm.FEATURES],train.y)
c=pd.read_csv(R/'data/raw/combine.csv',low_memory=False);c=c[c.season.between(2016,2017)].copy();c['position']=c.pos.map(tm.pos_group);c['height']=c.ht.map(lambda x:float(str(x).split('-')[0])*12+float(str(x).split('-')[1]) if '-' in str(x) else np.nan)
for repair in m['prospect']['identityRepairs']:
 mask=(c.season==repair['year'])&(c.player_name==repair['player'])&c.pfr_id.isna();c.loc[mask,'pfr_id']=repair['id']
norm=lambda s:re.sub('[^a-z0-9]','',str(s).lower())
college=lambda s:norm(str(s).replace(' St.',' State').replace('Southern California','USC').replace('Louisiana-Lafayette','Louisiana'))
c['canonical_id']=[f'p{r.season}-'+hashlib.sha256((norm(r.player_name)+'|'+college(r.school)).encode()).hexdigest()[:10] for r in c.itertuples()]
c=c[~c.position.isin(['K','P','LS'])].copy();c['raw_probability']=model.predict_proba(c[tm.FEATURES])[:,1];c['pool_probability']=np.nan;c['pool_size']=0;c['pool_key']='';groups=[]
for (year,position),sub in c.groupby(['season','position']):
 ordered=sorted(sub.index,key=lambda i:(round(float(c.loc[i,'raw_probability']),6),c.loc[i,'canonical_id']));chunks=[ordered[i:i+5] for i in range(0,len(ordered),5)]
 if len(chunks)>1 and len(chunks[-1])<5:chunks[-2].extend(chunks.pop())
 for j,chunk in enumerate(chunks):
  value=float(np.mean(np.round(c.loc[chunk,'raw_probability'],6)));key=f'{year}-{position}-{j}'
  c.loc[chunk,'pool_probability']=value;c.loc[chunk,'pool_size']=len(chunk);c.loc[chunk,'pool_key']=key;groups.append({'year':int(year),'position':position,'pool':j,'size':len(chunk),'meanProbability':value})
c[['season','canonical_id','position','raw_probability','pool_probability','pool_size','pool_key']].to_csv(A/'features/pooling_candidates.csv',index=False)
# Current-source unknown identifiers stay unlabeled, but contribute to grouping.
test=c[c.pfr_id.notna()].merge(labels[['season','pfr_id','y']],on=['season','pfr_id'],how='inner',validate='one_to_one');test['display_midpoint']=tm.probband(test.pool_probability)
raw=tm.binary(test.y,test.raw_probability);pooled=tm.binary(test.y,test.pool_probability);display=tm.binary(test.y,test.display_midpoint)
old=pd.read_csv(A/'outcomes/prospect_test_predictions.csv');check=old.merge(test[['season','pfr_id','raw_probability']],on=['season','pfr_id'],validate='one_to_one');assert len(check)==len(old);assert np.allclose(check.selected_probability,check.raw_probability,atol=1e-10)
result={'version':'shared-profile-heldout-validation-v1','asOf':'2026-11-02','train':[2013,2014],'tuning':[2015,2015],'test':[2016,2017],'groupingRule':'Per draft year and broad position; sort rounded6-digit model probability, chunk5, merge final short tail; arithmetic mean shared by group. Canonical ID lexicographic order breaks ties.','groupingUsesLabels':False,'allCandidatesGrouped':len(c),'evaluatedWithKnownLabels':len(test),'unknownLabelsExcluded':len(c)-len(test),'minimumGroupSize':min(x['size'] for x in groups),'groups':groups,'metrics':{'raw':raw,'pooledMean':pooled,'pooledTenPointDisplayMidpoint':display},'pairedDifferencesVsRaw':{'pooledMean':tm.paired(test.y,test.pool_probability,test.raw_probability,test.season),'pooledTenPointDisplayMidpoint':tm.paired(test.y,test.display_midpoint,test.raw_probability,test.season)},'limitations':['Utility evaluation only: does not prove anonymity or equal human decision quality.','Only two held-out cohorts with identifiable outcomes; unknown identities participate in grouping but are excluded from metrics.','The transformation has not been independently evaluated against determined linkage attacks or human football memory.','College and verified college production are absent from this predictor; no conclusion about their decision value.','Model outcome remains rookie200-snap participation, not five-year talent.']}
(A/'pooling_validation.json').write_text(json.dumps(result,indent=2)+'\n');test[['season','pfr_id','position','y','raw_probability','pool_probability','display_midpoint','pool_size','pool_key']].to_csv(A/'outcomes/pooling_test_predictions.csv',index=False)
print(json.dumps({k:result[k] for k in ['allCandidatesGrouped','evaluatedWithKnownLabels','unknownLabelsExcluded','minimumGroupSize','metrics','pairedDifferencesVsRaw']},indent=2))
