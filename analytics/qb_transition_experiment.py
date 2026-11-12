"""Bounded, pre-cutoff annual QB usage-transition research; never runtime data.

Protocol fixed before reading experiment outcomes: states 0,1-199,200-599,600+
scrimmage snaps; state-only versus state+early/later experience; shrinkage0/5/20.
Select by 2015 next-year CRPS using transitions ending2014; assess2016-17 with
transitions ending2015. A separate five-year2018 audit is explicitly exposed.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import five_year as fy
from forecast_audit import evaluate_distribution, summarize

ROOT=Path(__file__).resolve().parents[1];A=ROOT/'analytics'
SEED=20261112;DRAWS=8192


def state(snaps):
    return 0 if snaps==0 else 1 if snaps<200 else 2 if snaps<600 else 3


def load_panel():
    annual,coverage,_=fy.load_annual(2013,2017)
    combine=pd.read_csv(ROOT/'data/raw/combine.csv',low_memory=False)
    candidates=combine[combine.pos.eq('QB')&combine.season.between(2009,2017)].copy()
    unknown=candidates[candidates.pfr_id.isna()]
    known=candidates[candidates.pfr_id.notna()]
    if known.duplicated(['season','pfr_id']).any():raise ValueError('Ambiguous cohort identity')
    panel=[]
    for r in known.itertuples():
        for year in range(max(2013,int(r.season)),min(2017,int(r.season)+4)+1):
            observation=annual.get((year,r.pfr_id))
            # A known ID absent from a complete game source has zero recorded NFL
            # snaps. This does not identify retirement, injury, or roster status.
            panel.append({'cohort':int(r.season),'pfrId':r.pfr_id,'year':year,
                'experience':year-int(r.season),'snaps':observation['snaps'] if observation else 0,
                'games':observation['games'] if observation else 0,
                'sourcePresence':'recorded-player-row' if observation else 'known-id-absent-complete-season'})
    panel=pd.DataFrame(panel);lookup={(r.pfrId,r.year):r for r in panel.itertuples()};pairs=[]
    for r in panel.itertuples():
        previous=lookup.get((r.pfrId,r.year-1))
        if previous is None or r.experience<1:continue
        pairs.append({'pfrId':r.pfrId,'cohort':r.cohort,'year':r.year,'experience':r.experience,
            'prior':previous.snaps,'next':r.snaps,'nextGames':r.games,'priorState':state(previous.snaps),
            'labelAvailableBy':f'{r.year+1}-03-01'})
    return panel,pd.DataFrame(pairs),coverage,unknown[['season','player_name']].to_dict('records')


def transition_weights(train, prior, experience, variant):
    kind,k=variant
    age=(train.experience.to_numpy()==1)==(experience==1)
    parent=age if kind=='state+experience' and age.any() else np.ones(len(train),dtype=bool)
    local=parent & train.priorState.eq(state(prior)).to_numpy()
    n=int(local.sum());alpha=n/(n+k) if n else 0.
    w=parent.astype(float)/parent.sum()*(1-alpha)
    if n:w+=local.astype(float)/n*alpha
    if not np.isclose(w.sum(),1) or (w<0).any():raise ValueError('Invalid transition mixture')
    return w


def evaluate(train,test,variant=None,persistence=False):
    rows=[]
    for r in test.itertuples():
        if persistence:v=np.array([r.prior],dtype=float);w=np.array([1.])
        else:
            v=train.next.to_numpy(float)
            w=np.ones(len(train))/len(train) if variant is None else transition_weights(train,r.prior,r.experience,variant)
        active=w>0
        metric=evaluate_distribution(v[active],w[active],r.next)
        rows.append({'pfrId':r.pfrId,'year':r.year,**metric})
    return rows


def cluster_difference(first,baseline):
    d=pd.DataFrame({'id':[r['pfrId'] for r in first],
                    'difference':[r['crps']-b['crps'] for r,b in zip(first,baseline)]})
    clusters={key:g.difference.to_numpy() for key,g in d.groupby('id')};ids=list(clusters)
    rng=np.random.default_rng(SEED);boot=[]
    for _ in range(2000):
        chosen=rng.integers(0,len(ids),size=len(ids))
        boot.append(np.concatenate([clusters[ids[i]] for i in chosen]).mean())
    return {'meanCrpsDifference':float(d.difference.mean()),'playerClusterBootstrap95':list(map(float,np.quantile(boot,[.025,.975]))),
            'uniquePlayers':len(ids),'resamples':2000,
            'limitation':'Accounts for repeated players, not shared season/team context; only two assessment seasons.'}


def fit_choice(pairs):
    train=pairs[pairs.year<=2014];validation=pairs[pairs.year==2015]
    if train.empty or validation.empty:raise ValueError('Missing predeclared chronological split')
    candidates={}
    for kind in ['state','state+experience']:
        for k in [0,5,20]:
            key=f'{kind}:shrink{k}'
            candidates[key]={'variant':[kind,k],'metrics':summarize(evaluate(train,validation,(kind,k)))}
    selected=min(candidates,key=lambda key:(candidates[key]['metrics']['meanCrps'],key))
    return selected,candidates


def simulate_paths(panel,train,variant,probability,seed):
    rng=np.random.default_rng(seed)
    rookie=panel[panel.experience==0]
    positive=rookie.snaps.ge(200).to_numpy()
    if not positive.any() or positive.all():raise ValueError('Missing rookie strata')
    w=np.where(positive,probability/positive.sum(),(1-probability)/(~positive).sum())
    paths=np.empty((DRAWS,5),dtype=float)
    paths[:,0]=rng.choice(rookie.snaps.to_numpy(),size=DRAWS,p=w)
    for age in range(1,5):
        # Every next-year value is an actual observed QB annual snap count.
        # Combining rows into a path is a Markov assumption, not historical fact.
        previous_states=np.array([state(v) for v in paths[:,age-1]])
        for s in range(4):
            mask=previous_states==s
            if not mask.any():continue
            representative=[0,1,200,600][s]
            weights=transition_weights(train,representative,age,variant)
            paths[mask,age]=rng.choice(train.next.to_numpy(),size=int(mask.sum()),p=weights)
    return paths


def run():
    panel,pairs,coverage,unknown=load_panel()
    selected,candidates=fit_choice(pairs);variant=tuple(candidates[selected]['variant'])
    # Poison assessment outcomes: selection MUST remain exactly invariant.
    poison=pairs.copy();poison.loc[poison.year>=2016,'next']=999999
    assert fit_choice(poison)==(selected,candidates)
    train=pairs[pairs.year<=2015];test=pairs[pairs.year.isin([2016,2017])]
    selected_rows=evaluate(train,test,variant);baseline=evaluate(train,test)
    persistence=evaluate(train,test,persistence=True)
    test_ids=set(test.pfrId);train_ids=set(train.pfrId)
    # Final research proposal fit contains no post2017 transition observation.
    assert pairs.year.max()==2017
    assert (pd.to_datetime(pairs.labelAvailableBy,utc=True)<pd.Timestamp('2018-04-26',tz='UTC')).all()
    frozen=pd.read_csv(A/'five_year_frozen_2018_predictions.csv')
    qbs=frozen[frozen.position.eq('QB')].copy();five=[];annual_cov=[];seed_metrics=[]
    for r in qbs.itertuples():
        actual=np.array([getattr(r,f'snaps{i}') for i in range(1,6)])
        paths=simulate_paths(panel,pairs,variant,r.pooledRookieProbability,SEED+int(r.Index))
        totals=paths.sum(axis=1);unique,counts=np.unique(totals,return_counts=True)
        five.append(evaluate_distribution(unique,counts/counts.sum(),actual.sum()))
        lo,hi=np.quantile(paths,[.025,.975],axis=0)
        annual_cov.append(((actual>=lo)&(actual<=hi)).astype(float))
    for seed in [SEED+1,SEED+2,SEED+3]:
        rows=[]
        for r in qbs.itertuples():
            paths=simulate_paths(panel,pairs,variant,r.pooledRookieProbability,seed+int(r.Index))
            totals=paths.sum(axis=1);unique,counts=np.unique(totals,return_counts=True)
            rows.append(evaluate_distribution(unique,counts/counts.sum(),sum(getattr(r,f'snaps{i}') for i in range(1,6))))
        seed_metrics.append({'seed':seed,'metrics':summarize(rows)})
    support=[]
    for age_group in ['second-season','third-through-fifth']:
        for s in range(4):
            sub=pairs[(pairs.experience.eq(1) if age_group=='second-season' else pairs.experience.gt(1))&pairs.priorState.eq(s)]
            support.append({'experienceBand':age_group,'priorUsageState':s,'rows':len(sub),
                            'uniquePlayers':int(sub.pfrId.nunique()),'positiveNextYears':int(sub.next.gt(0).sum())})
    result={'version':'qb-annual-transition-research-v1','asOf':'2026-11-12','runtimeChanged':False,
        'protocol':{'states':['zero','1–199','200–599','600+'],'experienceBands':['second-season','third-through-fifth'],
            'shrinkagePseudoCounts':[0,5,20],'selectionTrainTransitionEndYear':2014,'selectionYear':2015,
            'assessmentTrainTransitionEndYear':2015,'assessmentYears':[2016,2017],'finalResearchFitThrough':2017,
            'selectionMetric':'Exact annual next-year CRPS','assessmentOutcomePoisoning':'passed',
            'fiveYearAuditStatus':'Already exposed2018 outcomes; not used for candidate fitting or selection.'},
        'data':{'panelRows':len(panel),'transitionRows':len(pairs),'uniqueTransitionPlayers':int(pairs.pfrId.nunique()),
                'unknownIdExclusions':unknown,'panelBySeason':panel.groupby('year').size().to_dict(),
                'knownIdAbsentRows':int(panel.sourcePresence.eq('known-id-absent-complete-season').sum()),
                'zeroToPositiveTransitions':int(((pairs.prior==0)&(pairs.next>0)).sum()),
                'assessmentPlayerOverlapWithTraining':len(test_ids&train_ids),'assessmentUniquePlayers':len(test_ids),
                'coverage':coverage},
        'selection':{'selected':selected,'candidates':candidates},
        'annualAssessment':{'selected':summarize(selected_rows),'unconditionalTransitionBaseline':summarize(baseline),
            'persistencePointBaseline':summarize(persistence),'pairedVsUnconditional':cluster_difference(selected_rows,baseline),
            'byYear':{str(year):summarize([r for r in selected_rows if r['year']==year]) for year in [2016,2017]}},
        'strict2018CandidateSupport':support,'rookie2013Through2017Support':{'rows':int(panel.experience.eq(0).sum()),
            'rolePositive':int((panel.experience.eq(0)&panel.snaps.ge(200)).sum())},
        'reusedFiveYear2018':{'n':len(qbs),'drawsPerProspect':DRAWS,'seed':SEED,'metrics':summarize(five),
            'annualCoverage95':list(map(float,np.mean(annual_cov,axis=0))),'additionalSeedDiagnostics':seed_metrics},
        'decision':'Research only. Annual transition performance cannot validate a five-year rookie trajectory. No runtime promotion or gate change.',
        'limitations':['Annual-state Markov assumption loses persistent latent ability and higher-order career dependence; first-order persistence alone is not sufficient.',
            'Predicted paths recombine observed annual outcomes across players; they are simulated estimates, never recorded careers.',
            'Selection and assessment use overlapping players. This tests a known-player annual forecast, not unseen-rookie career prediction.',
            'Known-ID absence means zero recorded NFL snaps in a fully reconciled source season, not proven retirement, injury or roster exclusion. Zero is not absorbing.',
            'Unknown PFR identities are excluded, never filled with zero; combine participation and identity selection bias remain.',
            'No independent strict pre2018 five-year trajectory assessment exists; annual validation and exposed2018 diagnostics cannot replace it.',
            'Year2013–17 snapshots lack archived original publication timestamps; label-availability dates are conservative reconstructed dates.',
            'No post2017 outcomes enter fit or selection. The investigation was motivated by exposed2018 support failures, so it is not a new untouched test.',
            'No empirical causal snaps-to-wins identification, injury model, specialist target, or parameter-uncertainty guarantee is added.'],
        'sources':{'methodology':'https://www.jstatsoft.org/article/view/v038i08','properScoring':'https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf'},
        'sourceHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__),A/'five_year.py',A/'forecast_audit.py',ROOT/'data/raw/games.csv',ROOT/'data/raw/combine.csv',A/'five_year_frozen_2018_predictions.csv']+[ROOT/f'data/raw/snap_counts_{y}.csv' for y in range(2013,2018)]}}
    (A/'qb_transition_experiment.json').write_text(json.dumps(result,indent=2)+'\n')
    panel.to_csv(A/'qb_transition_panel.csv',index=False);pairs.to_csv(A/'qb_transition_pairs.csv',index=False)
    pd.DataFrame(selected_rows).to_csv(A/'qb_transition_assessment_predictions.csv',index=False)
    print(json.dumps({'selected':selected,'annual':result['annualAssessment'],'fiveYear':result['reusedFiveYear2018'],'data':{k:v for k,v in result['data'].items() if k not in ['coverage','unknownIdExclusions']}},indent=2))
    return result


if __name__=='__main__':run()
