"""Research-only chronological 2016/2017 QB career hindcast; no runtime writes.

Run: python qb_five_year_hindcast.py --root REPOSITORY --out OUTPUT_DIRECTORY
"""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
import pandas as pd

DRAWS=8192
SEED=20261120


def distribution(draws,actual):
    # Exact empirical-draw CRPS in O(n log n), equivalent to pairwise definition.
    x=np.sort(np.asarray(draws,float));n=len(x)
    result={'actual':float(actual),'mean':float(x.mean()),
        'crps':float(np.abs(x-actual).mean()-np.sum((2*np.arange(1,n+1)-n-1)*x)/(n*n)),
        'outsideSupport':bool(actual<x[0] or actual>x[-1])}
    for level in [80,95]:
        alpha=1-level/100
        lo=x[max(0,int(np.ceil(alpha/2*n))-1)]
        hi=x[max(0,int(np.ceil((1-alpha/2)*n))-1)]
        result.update({f'lower{level}':float(lo),f'upper{level}':float(hi),
            f'intervalScore{level}':float(hi-lo+2/alpha*max(lo-actual,0)+2/alpha*max(actual-hi,0))})
    return result


def bootstrap(rows):
    # One five-year outcome per QB, stratified by forecast origin.
    cohorts=sorted(set(r['cohort'] for r in rows));rng=np.random.default_rng(SEED)
    groups=[np.array([r['transition']['crps']-r['persistence']['crps'] for r in rows if r['cohort']==year]) for year in cohorts]
    draws=[np.concatenate([g[rng.integers(0,len(g),len(g))] for g in groups]).mean() for _ in range(5000)]
    return {'meanCrpsDifference':float(np.mean(np.concatenate(groups))),
        'playerBootstrap95':list(map(float,np.quantile(draws,[.025,.975]))),
        'resamples':5000,'stratifiedByCohort':True,
        'limitation':'Player resampling conditions on fitted empirical models; two cohorts cannot estimate between-era, team, or parameter uncertainty.'}


def run(root,out):
    sys.path.insert(0,str(root/'analytics'))
    import qb_transition_experiment as q
    import five_year as fy
    from forecast_audit import summarize,evaluate_distribution
    # Check efficient scoring against the original finite-mixture expression.
    x=np.array([0.,0.,200.,900.]);assert abs(distribution(x,300)['crps']-evaluate_distribution(x,np.ones(4)/4,300)['crps'])<1e-10
    panel,pairs,_,unknown=q.load_panel()
    selected,candidates=q.fit_choice(pairs);variant=tuple(candidates[selected]['variant'])
    poison=pairs.copy();poison.loc[poison.year>=2016,'next']=999999
    assert q.fit_choice(poison)==(selected,candidates)
    # Evaluation outcomes are loaded separately and never passed to prediction.
    annual,coverage,_=fy.load_annual(2016,2021)
    combine=pd.read_csv(root/'data/raw/combine.csv',low_memory=False)
    targets=combine[combine.pos.eq('QB')&combine.season.isin([2016,2017])]
    excluded=targets[targets.pfr_id.isna()][['season','player_name']].to_dict('records')
    targets=targets[targets.pfr_id.notna()].copy()
    if targets.duplicated(['season','pfr_id']).any():raise ValueError('Duplicate QB identities')
    rows=[];annual_rows=[];origins=[];seed_results=[];dependence={}
    def predictions(cohort,seed):
        fit_panel=panel[panel.year<cohort].copy();fit_pairs=pairs[pairs.year<cohort].copy()
        rookie=fit_panel[fit_panel.experience.eq(0)]
        p=float(rookie.snaps.ge(200).mean())
        paths=q.simulate_paths(fit_panel,fit_pairs,variant,p,seed)
        # Reuse the same sampled rookie values for paired initialization.
        persistence=np.repeat(paths[:,0,None],5,axis=1)
        exposure=np.array([17/16 if cohort+age>=2021 else 1 for age in range(5)])
        return paths*exposure,persistence*exposure,fit_panel,fit_pairs,p
    for cohort,cutoff in [(2016,'2016-04-28'),(2017,'2017-04-27')]:
        paths,persistence,fit_panel,fit_pairs,p=predictions(cohort,SEED+cohort)
        assert pd.to_datetime(fit_pairs.labelAvailableBy,utc=True).max()<pd.Timestamp(cutoff,tz='UTC')
        # Explicit invariance to excluded, later observations.
        original=q.simulate_paths(fit_panel,fit_pairs,variant,p,SEED+cohort)
        contaminated=panel.copy();contaminated.loc[contaminated.year>=cohort,'snaps']=999999
        contaminated_pairs=pairs.copy();contaminated_pairs.loc[contaminated_pairs.year>=cohort,'next']=999999
        np.testing.assert_array_equal(original,q.simulate_paths(contaminated[contaminated.year<cohort],contaminated_pairs[contaminated_pairs.year<cohort],variant,p,SEED+cohort))
        group=targets[targets.season.eq(cohort)]
        origins.append({'cohort':cohort,'informationCutoff':cutoff+'T00:00:00Z',
            'latestFitOutcomeSeason':cohort-1,'latestFitLabelAvailableBy':str(fit_pairs.labelAvailableBy.max()),
            'panelRows':len(fit_panel),'transitionRows':len(fit_pairs),'uniqueTransitionPlayers':int(fit_pairs.pfrId.nunique()),
            'rookieRows':int(fit_panel.experience.eq(0).sum()),'rookieRoleProbability':p,
            'testPlayers':len(group),'outcomeSeasons':[cohort,cohort+4],
            'fiveYearLabelAvailableBy':f'{cohort+5}-03-01','futureOutcomePoisoningPassed':True})
        for r in group.itertuples():
            actual=np.array([annual.get((cohort+age,r.pfr_id),{'snaps':0})['snaps'] for age in range(5)])
            record={'cohort':cohort,'pfrId':r.pfr_id,'playerName':r.player_name,'actualAnnual':actual.tolist(),
                'transition':distribution(paths.sum(axis=1),actual.sum()),'persistence':distribution(persistence.sum(axis=1),actual.sum())}
            rows.append(record)
            for age in range(5):annual_rows.append({'cohort':cohort,'pfrId':r.pfr_id,'age':age,
                'transition':distribution(paths[:,age],actual[age]),'persistence':distribution(persistence[:,age],actual[age])})
        observed=np.array([r['actualAnnual'] for r in rows if r['cohort']==cohort])
        dependence[str(cohort)]={'observedAnnualPearson':np.corrcoef(observed.T).tolist(),
            'transitionAnnualPearson':np.corrcoef(paths.T).tolist(),
            'persistenceAnnualPearson':np.corrcoef(persistence.T).tolist(),
            'limitation':'Observed matrices have only 15 or 17 careers. Simulated rows recombine people; matching correlations alone cannot establish joint calibration.'}
        for seed in [SEED+100,SEED+200,SEED+300]:
            a,b,*_=predictions(cohort,seed+cohort)
            ar=[distribution(a.sum(axis=1),r['transition']['actual']) for r in rows if r['cohort']==cohort]
            br=[distribution(b.sum(axis=1),r['persistence']['actual']) for r in rows if r['cohort']==cohort]
            seed_results.append({'cohort':cohort,'seed':seed+cohort,'transitionCrps':float(np.mean([r['crps'] for r in ar])),
                'persistenceCrps':float(np.mean([r['crps'] for r in br]))})
    def metrics(group):return {**{name:summarize([r[name] for r in group]) for name in ['transition','persistence']},'pairedCrps':bootstrap(group)}
    report={'version':'qb-five-year-chronological-hindcast-v1','asOf':'2026-11-20','runtimeChanged':False,
        'status':'Previously exposed historical cohorts; research only, no new untouched test or production promotion.',
        'protocol':{'selected':selected,'variant':list(variant),'selectionTrainingEnds':2014,'selectionLabels':2015,
            'selectionLabelAvailableBy':'2016-03-01','selectionMetric':'exact annual CRPS','selectionPoisoningPassed':True,
            'draws':DRAWS,'seed':SEED,'rookieInitialization':'Unconditional empirical QB rookie snaps available before each origin; identical sampled rookie values for both candidates. No later-selected combine classifier.',
            'persistence':'Repeat sampled rookie snap count across all five future seasons, then apply the common schedule-exposure multiplier. Does not condition on target rookie actual.',
            'exposure':'Both candidates scale annual snaps by target scheduled games/16; only 2021 in the 2017 horizon is scaled.',
            'parameterSelection':'Reuse existing 2015-selected candidate; no hindcast outcome selects states, shrinkage, or initialization.'},
        'origins':origins,'overall':metrics(rows),'byCohort':{str(c):metrics([r for r in rows if r['cohort']==c]) for c in [2016,2017]},
        'annualByAge':{str(age+1):metrics([r for r in annual_rows if r['age']==age]) for age in range(5)},
        'trajectoryDependence':dependence,'additionalSeeds':seed_results,'excludedUnknownTargetIds':excluded,'sourceCoverage':coverage,
        'limitations':['Only two small, previously exposed cohorts; hypothesis motivated by exposed 2018 failures.',
            'First-order state transitions recombine players and lose latent ability and higher-order dependence.',
            'Empirical rookie initialization is unconditional within QB; does not establish personalized rookie forecast quality.',
            'Known-ID combine selection bias remains; known-ID absence in complete annual files is zero recorded snaps, not proven retirement or injury.',
            'Original source publication timestamps are unavailable; March 1 label dates and combine event availability are reconstructed.',
            'No contemporaneous complete five-year donor comparator exists at 2016/2017 origins; later donor careers would leak future labels.',
            'Finite empirical-draw distributions are numerical approximations; seed checks do not capture parameter uncertainty.',
            'No causal wins validation, gate change, or runtime model promotion.'],
        'sourceHashes':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'analytics/qb_transition_experiment.py',root/'analytics/five_year.py',root/'analytics/forecast_audit.py',root/'data/raw/combine.csv',root/'data/raw/games.csv']+[root/f'data/raw/snap_counts_{year}.csv' for year in range(2013,2022)]},
        'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out.mkdir(parents=True,exist_ok=True)
    (out/'qb_five_year_hindcast.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'qb_five_year_hindcast_predictions.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'qb_five_year_hindcast_annual_predictions.json').write_text(json.dumps(annual_rows,indent=2)+'\n')
    print(json.dumps({'overall':report['overall'],'origins':origins},indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();run(args.root,args.out)
