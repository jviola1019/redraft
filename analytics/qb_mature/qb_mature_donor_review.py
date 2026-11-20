"""Untuned, cutoff-safe rolling mature-QB-donor research. Writes explicit out only."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
import pandas as pd

SEED=20261120


def paired(rows):
    rng=np.random.default_rng(SEED)
    groups=[np.array([r['candidate']['crps']-r['baseline']['crps'] for r in rows if r['cohort']==c]) for c in sorted(set(r['cohort'] for r in rows))]
    draws=[np.concatenate([v[rng.integers(0,len(v),len(v))] for v in groups]).mean() for _ in range(5000)]
    return {'difference':float(np.concatenate(groups).mean()),'playerBootstrap95':list(map(float,np.quantile(draws,[.025,.975]))),'resamples':5000,'stratifiedByOrigin':True,'limitation':'Conditions on empirical fitted distributions; only three cohorts, no between-era or parameter-uncertainty guarantee.'}


def run(root,out):
    sys.path.insert(0,str(root/'analytics'))
    import five_year as fy
    from forecast_audit import summarize,evaluate_distribution
    protocol=(Path(__file__).parent/'PROTOCOL.md').read_bytes()
    # Reconciliation rejects missing games and header-only seasons.
    annual,coverage,_=fy.load_annual(2013,2025)
    combine=pd.read_csv(root/'data/raw/combine.csv',low_memory=False)
    qbs=combine[combine.pos.eq('QB')&combine.season.between(2013,2021)].copy()
    excluded=qbs[qbs.pfr_id.isna()][['season','player_name']].to_dict('records')
    qbs=qbs[qbs.pfr_id.notna()].copy()
    assert not qbs.duplicated(['season','pfr_id']).any()
    vectors={r.pfr_id:np.array([annual.get((r.season+age,r.pfr_id),{'snaps':0})['snaps'] for age in range(5)],float) for r in qbs.itertuples()}
    rows=[];origins=[];annual_rows=[]
    def values(donors,origin):
        return np.array([vectors[r.pfr_id]/np.array([17 if r.season+age>=2021 else 16 for age in range(5)])*np.array([17 if origin+age>=2021 else 16 for age in range(5)]) for r in donors.itertuples()])
    for origin,cutoff in [(2019,'2019-04-25'),(2020,'2020-04-23'),(2021,'2021-04-29')]:
        candidate=qbs[qbs.season<=origin-5];baseline=qbs[qbs.season.eq(2013)];target=qbs[qbs.season.eq(origin)]
        assert all(f'{int(year)+5}-03-01'<cutoff for year in candidate.season)
        a=values(candidate,origin);b=values(baseline,origin)
        origins.append({'origin':origin,'informationCutoff':cutoff+'T00:00:00Z','donorCohorts':sorted(map(int,candidate.season.unique())),
            'donorPlayers':len(candidate),'baselineDonors':len(baseline),'testPlayers':len(target),
            'lastFitOutcomeSeason':origin-1,'lastFitLabelAvailableBy':f'{origin}-03-01',
            'evaluationOutcomeSeasons':[origin,origin+4],'evaluationLabelAvailableBy':f'{origin+5}-03-01',
            'candidateMaximumTotal':float(a.sum(axis=1).max()),'baselineMaximumTotal':float(b.sum(axis=1).max()),
            'candidateMaximumCareerPfrId':candidate.iloc[int(np.argmax(a.sum(axis=1)))].pfr_id})
        # Filtering donors before transformation prevents later cohorts from entering fit.
        poison={pid:v.copy() for pid,v in vectors.items()}
        for r in qbs[qbs.season>origin-5].itertuples():poison[r.pfr_id][:]=999999
        av=np.array([poison[r.pfr_id] for r in candidate.itertuples()]);assert np.array_equal(av,np.array([vectors[r.pfr_id] for r in candidate.itertuples()]))
        for r in target.itertuples():
            actual=vectors[r.pfr_id]
            rows.append({'cohort':origin,'pfrId':r.pfr_id,'actualAnnual':actual.astype(int).tolist(),
                'candidate':evaluate_distribution(a.sum(axis=1),np.ones(len(a))/len(a),actual.sum()),
                'baseline':evaluate_distribution(b.sum(axis=1),np.ones(len(b))/len(b),actual.sum())})
            for age in range(5):annual_rows.append({'cohort':origin,'pfrId':r.pfr_id,'age':age,
                'candidate':evaluate_distribution(a[:,age],np.ones(len(a))/len(a),actual[age]),
                'baseline':evaluate_distribution(b[:,age],np.ones(len(b))/len(b),actual[age])})
    def metrics(group):return {**{k:summarize([r[k] for r in group]) for k in ['candidate','baseline']},'pairedCrps':paired(group)}
    report={'version':'qb-mature-donor-rolling-v1','asOf':'2026-11-20','runtimeChanged':False,'protocolSha256':hashlib.sha256(protocol).hexdigest(),
        'candidate':'Equal-weight whole QB donor careers from all cohorts fully matured by origin; no hyperparameter tuning.',
        'baseline':'Equal-weight2013 QB careers at every origin; both forecasts unconditional within QB.',
        'origins':origins,'overall':metrics(rows),'byCohort':{str(c):metrics([r for r in rows if r['cohort']==c]) for c in [2019,2020,2021]},
        'annualByAge':{str(age+1):metrics([r for r in annual_rows if r['age']==age]) for age in range(5)},
        'unknownIdExclusions':excluded,'sourceCoverage':coverage,'futureCohortPoisoningPassed':True,
        'adoptionVerdict':'Research only. Later mature careers cannot repair strict2018 cutoff; rolling three-cohort unconditional evidence does not justify production promotion or personalized calibration.',
        'limitations':['Historical cohorts previously exposed elsewhere; not a newly untouched evaluation.',
            'Retrospective database identities and downloaded measurements lack original archived availability timestamps; March1 dates reconstructed.',
            'Known-ID combine selection; unknown identities excluded. Complete-source known-ID absence is zero recorded NFL snaps, not retirement or injury.',
            'Three cohorts cannot establish calibration across eras. Exact empirical integration removes numerical draw error only.',
            'No role-conditioning comparison; personalized runtime probabilities and causal wins are unvalidated by this candidate.',
            'Pooling later fully observed careers changes population support, not intrinsic player ability or causal opportunity.'],
        'sourceHashes':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'analytics/five_year.py',root/'analytics/forecast_audit.py',root/'data/raw/combine.csv',root/'data/raw/games.csv']+[root/f'data/raw/snap_counts_{year}.csv' for year in range(2013,2026)]},
        'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out.mkdir(parents=True,exist_ok=True)
    (out/'qb_mature_donor_review.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'qb_mature_donor_predictions.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'qb_mature_donor_annual_predictions.json').write_text(json.dumps(annual_rows,indent=2)+'\n')
    print(json.dumps({'origins':origins,'overall':report['overall']},indent=2));return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();run(args.root,args.out)
