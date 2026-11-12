"""Research-release gates. Software success does not imply statistical validity.

Exit 0: every declared gate passed. Exit 2: completed audit with retained failures
or unsupported/stale evidence. Exit 1: audit could not execute. --report-only
suppresses exit 2 for interactive inspection; it never changes report statuses.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
A = ROOT/'analytics'
TEAMS = ['CLE','KC','NE','SF']
REQUIRED_HASHES = ['lib/engine.ts','lib/simulation.ts','lib/scouting.ts',
                   'analytics/model.json','analytics/five_year_strict_2018.json',
                   'analytics/scoring_recalibration.json','data/processed/scenario-2018.json',
                   'lib/server-data.ts','data/clean/team_context_2018.json',
                   'data/clean/team_context_source_manifest.json']
REQUIRED_HASHES = sorted(set(REQUIRED_HASHES +
    [str(p.relative_to(ROOT)) for p in (ROOT/'data/processed').glob('scenario-*.json')] +
    [str(p.relative_to(ROOT)) for p in A.glob('model-*.json')]))
POLICY = {'version':'research-release-gates-2026-11-04-v1',
    'minimumDonorsPerConditionalStratum':10,
    'minimumSubgroupNominal95Coverage':.90,
    'maximumWinDifferenceMCSE':.25,
    'maximumImprovementProbabilityMCSE':.032,
    'minimumSimulationReplicates':256,
    'disclosure':'Engineering release tolerances established after prior diagnostics were seen; not preregistered scientific significance criteria. Subgroup rates are descriptive, no multiplicity-adjusted population claim.'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    audit = json.loads((A/'forecast_audit.json').read_text())
    strict = json.loads((A/'five_year_strict_2018.json').read_text())
    research = json.loads((A/'five_year_research.json').read_text())
    gates = []

    def add(key, status, evidence, requirement, scope):
        gates.append({'id':key,'status':status,'scope':scope,
                      'requirement':requirement,'evidence':evidence})

    # Saved predictions must continue to reproduce the reported frozen forecast.
    p = pd.read_csv(A/'five_year_frozen_2018_predictions.csv')
    y = p[[f'snaps{i}' for i in range(1,6)]].sum(axis=1).to_numpy()
    rmse = float(np.sqrt(np.mean((y-p.predictedTotalSnaps.to_numpy())**2)))
    expected = research['frozen2018ProductionModel']['metrics']['totalRMSE']
    add('frozen_metrics_recompute','pass' if abs(rmse-expected)<1e-8 else 'fail',
        {'computedRMSE':rmse,'storedRMSE':expected},'Saved predictions reproduce metrics','evidence-integrity')
    labels = pd.read_csv(A/'five_year_strict_labels.csv')
    cutoff_ok = bool((pd.to_datetime(labels.labelAvailableBy,utc=True)<pd.Timestamp(strict['cutoff'])).all())
    add('strict_label_cutoff','pass' if cutoff_ok else 'fail',
        {'cohorts':strict['cohorts'],'lastLabelAvailableBy':labels.labelAvailableBy.max()},
        'Every five-season donor label complete before draft cutoff','temporal-integrity')
    add('strict_independent_chronological_validation',
        'pass' if strict['validation']['chronologicallyValidatedFor2018'] else 'unsupported',
        strict['validation']['reason'],'An independent pre2018 five-year chronological test','forecast-validity')
    for filename, current in audit['sourceHashes'].items():
        actual = digest(ROOT/filename)
        add('forecast_source_'+filename,'pass' if current==actual else 'stale',
            {'evaluated':current,'current':actual},'Exact audit matches source artifact','evidence-integrity')
    for position, row in audit['subgroups'].items():
        support = row['support']
        sufficient = min(support['rookieRole'],support['noRookieRole']) >= POLICY['minimumDonorsPerConditionalStratum']
        add('conditional_support_'+position,'pass' if sufficient else 'unsupported',support,
            'At least10 donors in each conditional stratum; minimum screening rule, not proof of validity','forecast-support')
        for target in ['snaps','games']:
            interval = row[target]['interval95']
            add(f'coverage95_{position}_{target}',
                'pass' if interval['coverage']>=POLICY['minimumSubgroupNominal95Coverage'] else 'fail',
                {'n':row[target]['n'],**interval,
                 'outsideDonorSupport':row[target]['outsideDonorSupport']},
                'Nominal95% empirical interval covers at least90% of reused2018 subgroup outcomes','forecast-calibration')
    add('specialist_quality','unsupported',audit['specialists'],
        'Position-appropriate validated specialist quality target','forecast-validity')
    improvement = audit['pairedCrpsVsPositionBaseline']
    add('forecast_distribution_skill',
        'pass' if improvement['playerBootstrap95'][1]<0 else 'unsupported',improvement,
        'Paired CRPS improvement confidence interval excludes zero on independent evidence; reused cohort only supports an audit','forecast-validity')
    add('counterfactual_snaps_to_wins','unsupported',
        'Participation forecasts precede unvalidated opportunity and snaps-to-wins transformations.',
        'Validated effect mapping with sensitivity and identification limitations','counterfactual-validity')

    simulations = {}
    for team in TEAMS:
        path = A/('simulation_diagnostics'+('' if team=='CLE' else '_'+team)+'.json')
        if not path.exists():
            add('simulation_'+team,'unsupported',str(path),'Four declared scenario diagnostics present','simulation-validity')
            continue
        d = json.loads(path.read_text())
        stale = []
        for name in REQUIRED_HASHES:
            if not (ROOT/name).exists() or d.get('sourceHashes',{}).get(name)!=digest(ROOT/name):
                stale.append(name)
        add('simulation_fresh_'+team,'stale' if stale else 'pass',
            {'mismatches':stale,'configuration':d.get('configuration')},
            'Diagnostic hashes match every current runtime dependency','evidence-integrity')
        add('simulation_replicates_'+team,
            'pass' if d.get('replicates',0)>=POLICY['minimumSimulationReplicates'] else 'fail',
            d.get('replicates'),'At least256 paired five-season replicates','monte-carlo-precision')
        convergence = d['convergence'][-1]
        add('simulation_precision_'+team,
            'pass' if convergence['pairedStandardError']<=POLICY['maximumWinDifferenceMCSE'] and convergence['probabilityMcse']<=POLICY['maximumImprovementProbabilityMCSE'] else 'fail',
            convergence,'Win-difference MCSE≤.25 wins and improvement-probability MCSE≤.032','monte-carlo-precision')
        add('simulation_distribution_'+team,'fail' if d['distributionFlags'] else 'pass',
            d['distributionFlags'],
            'Observed2018–22 summary inside conditional simulated2.5–97.5% range; diagnostic, not calibrated model-uncertainty interval','simulation-validity')
        simulations[team]={'configuration':d['configuration'],'stale':bool(stale),
                           'replicates':d['replicates'],'flags':d['distributionFlags'],
                           'convergence':convergence}
    counts = {s:sum(g['status']==s for g in gates) for s in ['pass','fail','unsupported','stale']}
    result = {'version':POLICY['version'],'asOf':datetime.now(timezone.utc).date().isoformat(),'policy':POLICY,
        'releaseStatus':'pass' if all(g['status']=='pass' for g in gates) else 'blocked',
        'counts':counts,'gates':gates,'simulationScenarios':simulations,
        'seedAudit':{'count':len(audit['finiteEnsembleSeeds']),
            'seeds':[r['seed'] for r in audit['finiteEnsembleSeeds']],
            'drawsPerProspect':256,
            'rmsMeanApproximationErrorRange':[min(r['rmsMeanApproximationError'] for r in audit['finiteEnsembleSeeds']),max(r['rmsMeanApproximationError'] for r in audit['finiteEnsembleSeeds'])],
            'note':'Numerical precision audit only; more seeds cannot remedy donor support or causal validity.'},
        'interpretation':['Failed and unsupported gates block a claim of statistically validated full production.',
            'Structural software tests can pass while these research-release gates remain blocked.',
            'An individual gate pass does not establish calibrated forecasts for all subgroups or causal effects.',
            '2018–22 outcomes have been examined before: these are reused backtests, never an untouched final test.',
            'No thresholds are silently relaxed to turn an adverse result into success.']}
    (A/'statistical_gates.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Statistical release gates','',
        'The research release is **'+result['releaseStatus']+'**. This is a statistical evidence decision, separate from software test success.','',
        f"Counts: {counts['pass']} pass; {counts['fail']} fail; {counts['unsupported']} unsupported; {counts['stale']} stale.",'',
        'The criteria are disclosed engineering tolerances chosen after earlier results were reviewed. They are not a preregistered hypothesis test. The 2018 outcomes are reused backtests.','',
        '| Gate | Status | Requirement |','|---|---|---|']
    lines += [f"| {g['id']} | {g['status']} | {g['requirement']} |" for g in gates]
    lines += ['','Full measurements, subgroup uncertainty, source hashes and fixed seeds are in `statistical_gates.json` and `forecast_audit.json`.','',
        'Run `python analytics/forecast_audit.py` then `python analytics/statistical_gates.py`. Exit2 means the audit completed and retained adverse or unsupported evidence. Exit1 means execution failed. `--report-only` never changes the report status.','']
    (A/'STATISTICAL_GATES.md').write_text('\n'.join(lines))
    print(json.dumps({'releaseStatus':result['releaseStatus'],'counts':counts,
                      'adverse':[{'id':g['id'],'status':g['status']} for g in gates if g['status']!='pass']},indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--report-only',action='store_true')
    args=parser.parse_args()
    result=run()
    raise SystemExit(0 if args.report_only or result['releaseStatus']=='pass' else 2)
