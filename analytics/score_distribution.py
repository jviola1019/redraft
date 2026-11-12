"""Pre-cutoff two-part shutout experiment, with explicitly frozen time splits.

Protocol: candidate shutout probability window selection on 2014-15 only, with fits ending 2013;
final pre-2018 check on 2016-17 with fits ending 2015; then fit the selected
intercept-only rate window through 2017 for a known-exposed 2018-25 diagnostic. 2026 is
incomplete. The scoring law itself is the existing correlated normal score
model, conditioned on either shutout or no shutout. A separate pre-cutoff
logistic probability governs the hurdle event. No post-2017 data enters model
choice or runtime parameters; no runtime artifacts or release gates are edited.
"""
from pathlib import Path
import hashlib, json, math
import numpy as np
import pandas as pd
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
A = ROOT/'analytics'; RAW = ROOT/'data/raw/games.csv'; MODEL = A/'model.json'
SEED=20261112; N_BASE=32768; N_FORECAST=2048
ALIASES={'OAK':'LV','SD':'LAC','STL':'LA'}


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def nfl_scores(total, margin, tie_u):
    hs=np.maximum(0,np.floor((total+margin)/2+0.5)).astype(int)
    aws=np.maximum(0,np.floor((total-margin)/2+0.5)).astype(int)
    hs=np.where(hs==1,2,hs); aws=np.where(aws==1,2,aws)
    tied=hs==aws; break_tie=tied & (tie_u>.12)
    home_win=tie_u <= 1/(1+np.exp(-margin/8))
    hs=hs+(break_tie & home_win)*3; aws=aws+(break_tie & ~home_win)*3
    return hs,aws

def crps(sample,y):
    x=np.sort(np.asarray(sample,dtype=float)); n=len(x)
    pair=2*np.sum((2*np.arange(1,n+1)-n-1)*x)/(n*n)
    return float(np.mean(np.abs(x-y))-.5*pair)

def add_prior_context(g):
    # Team PF-PA/game at end of the preceding season only; relocation aliases mapped.
    sums={}
    for r in g.itertuples(index=False):
        for team,pf,pa in [(r.home_team,r.home_score,r.away_score),(r.away_team,r.away_score,r.home_score)]:
            k=(int(r.season),team); v=sums.setdefault(k,[0.,0.,0])
            v[0]+=float(pf); v[1]+=float(pa); v[2]+=1
    g=g.copy()
    g['home_prior']=[((sums.get((int(y)-1,h),[0,0,1])[0]-sums.get((int(y)-1,h),[0,0,1])[1])/max(1,sums.get((int(y)-1,h),[0,0,1])[2])) for y,h in zip(g.season,g.home_team)]
    g['away_prior']=[((sums.get((int(y)-1,a),[0,0,1])[0]-sums.get((int(y)-1,a),[0,0,1])[1])/max(1,sums.get((int(y)-1,a),[0,0,1])[2])) for y,a in zip(g.season,g.away_team)]
    g['total']=g.home_score+g.away_score; g['margin']=g.home_score-g.away_score
    g['shutout']=(g.home_score==0)|(g.away_score==0)
    return g

def fit_score_law(g, through):
    tr=g[(g.season>=2000)&(g.season<=through)]
    x=np.column_stack([np.ones(len(tr)),tr.home_prior-tr.away_prior])
    coef=np.linalg.lstsq(x,tr.margin.to_numpy(float),rcond=None)[0]
    rm=tr.margin.to_numpy(float)-x@coef
    rt=tr.total.to_numpy(float)-float(tr.total.mean())
    corr=float(np.corrcoef(rm,rt)[0,1])
    return {'homeAdvantage':float(coef[0]),'strengthCoefficient':float(coef[1]),
            'meanTotal':float(tr.total.mean()),'marginSd':float(rm.std(ddof=2)),
            'totalSd':float(rt.std(ddof=1)),'rho':corr,'fitThroughSeason':int(through)}

def expected_margin(df, law):
    return law['homeAdvantage']+law['strengthCoefficient']*(df.home_prior.to_numpy()-df.away_prior.to_numpy())

def fit_hurdle(train, window):
    # Only an intercept is fitted; the selected recency window controls the rate.
    rows=train[(train.season>=train.season.max()-window+1)]
    p=float(np.clip(rows.shutout.mean(),1e-6,1-1e-6))
    return {'form':'intercept_only','windowSeasons':int(window),
      'windowFirstSeason':int(rows.season.min()),'windowLastSeason':int(rows.season.max()),
      'shutoutRate':p,'intercept':float(math.log(p/(1-p))),
      'fitThroughSeason':int(train.season.max())}

def predict_p(df, law, hurdle):
    return np.full(len(df),hurdle['shutoutRate'])

def event_metrics(y,p):
    p=np.clip(np.asarray(p),1e-9,1-1e-9); y=np.asarray(y,dtype=float)
    return {'games':int(len(y)),'observedRate':float(y.mean()),'predictedRate':float(p.mean()),
      'brier':float(np.mean((p-y)**2)),'logLoss':float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)))}

def base_draw(row,law,rng,n):
    z1,z2=rng.standard_normal((2,n)); rho=law['rho']
    m=law['homeAdvantage']+law['strengthCoefficient']*(row.home_prior-row.away_prior)+z1*law['marginSd']
    t=np.maximum(6,law['meanTotal']+(rho*z1+math.sqrt(max(0,1-rho*rho))*z2)*law['totalSd'])
    hs,aws=nfl_scores(t,m,rng.random(n))
    return hs,aws

def score_forecast(df,law,hurdle,method,seed):
    rng=np.random.default_rng(seed); rows=[]
    ps=predict_p(df,law,hurdle) if method=='hurdle' else None
    for j,row in enumerate(df.itertuples(index=False)):
        bh,ba=base_draw(row,law,rng,N_BASE)
        if method=='normal':
            hs,aws=bh[:N_FORECAST],ba[:N_FORECAST]
            pzero=float(np.mean((bh==0)|(ba==0)))
        else:
            zero=(bh==0)|(ba==0); pos=~zero
            # Exact mixture weight comes from the separate intercept hurdle model.
            branch=rng.random(N_FORECAST)<ps[j]
            if not zero.any(): raise RuntimeError('No conditional shutout support in base score law.')
            if not pos.any(): raise RuntimeError('No conditional positive support in base score law.')
            iz=rng.integers(0,zero.sum(),size=N_FORECAST); ip=rng.integers(0,pos.sum(),size=N_FORECAST)
            zh,za=bh[zero],ba[zero]; ph,pa=bh[pos],ba[pos]
            hs=np.where(branch,zh[iz],ph[ip]); aws=np.where(branch,za[iz],pa[ip])
            pzero=float(ps[j])
        yt=int(row.total); ym=int(row.margin); shut=bool(row.shutout); tie=bool(row.home_score==row.away_score)
        tot=hs+aws; mar=hs-aws
        qtot=np.quantile(tot,[.05,.10,.90,.95]); qmar=np.quantile(mar,[.05,.10,.90,.95])
        rows.append({'season':int(row.season),'actualShutout':shut,'actualTie':tie,
          'totalMAE':abs(float(tot.mean())-yt),'marginMAE':abs(float(mar.mean())-ym),
          'totalCRPS':crps(tot,yt),'marginCRPS':crps(mar,ym),
          'total80':qtot[1]<=yt<=qtot[2],'total90':qtot[0]<=yt<=qtot[3],
          'margin80':qmar[1]<=ym<=qmar[2],'margin90':qmar[0]<=ym<=qmar[3],
          'pShutout':pzero,'pTie':float(np.mean(hs==aws))})
    return rows

def summarize(rows):
    d=pd.DataFrame(rows); ev=event_metrics(d.actualShutout.astype(int),d.pShutout)
    return {'games':len(d),'totalMAE':float(d.totalMAE.mean()),'marginMAE':float(d.marginMAE.mean()),
      'totalCRPS':float(d.totalCRPS.mean()),'marginCRPS':float(d.marginCRPS.mean()),
      'total80Coverage':float(d.total80.mean()),'total90Coverage':float(d.total90.mean()),
      'margin80Coverage':float(d.margin80.mean()),'margin90Coverage':float(d.margin90.mean()),
      'predictedShutoutRate':ev['predictedRate'],'observedShutoutRate':ev['observedRate'],
      'shutoutBrier':ev['brier'],'shutoutLogLoss':ev['logLoss'],
      'predictedTieRate':float(d.pTie.mean()),'observedTieRate':float(d.actualTie.mean())}

def runtime_score_law():
    t=json.loads(MODEL.read_text())['team']
    return {'homeAdvantage':t['homeAdvantage'],'strengthCoefficient':t['strengthCoefficient'],
      'meanTotal':t['meanTotal'],'marginSd':t['gameMarginSd'],
      'totalSd':t['residualTotalSd'],'rho':t['residualCorrelation'],
      'fitThroughSeason':int(t['fitThroughSeason'])}

def evaluated(g, train_through, test_years, selected_window, law_override=None):
    law=law_override or fit_score_law(g,train_through)
    train=g[(g.season>=2000)&(g.season<=train_through)]
    h=fit_hurdle(train,selected_window)
    test=g[g.season.isin(test_years)].copy()
    p=predict_p(test,law,h)
    normal_h={'form':'constant','intercept':0,'slope':0,'absExpectedMarginCenter':0,'absExpectedMarginScale':1,'fitThroughSeason':train_through}
    nr=score_forecast(test,law,normal_h,'normal',SEED)
    hr=score_forecast(test,law,h,'hurdle',SEED)
    return {'trainThroughSeason':train_through,'testSeasons':test_years,'scoreLaw':law,'hurdleParameters':h,
      'eventForecastMetrics':event_metrics(test.shutout.astype(int),p),
      'scoreMetrics':{'currentCorrelatedNormal':summarize(nr),'twoPartHurdle':summarize(hr)},
      'bySeason':{'currentCorrelatedNormal':{str(y):summarize([r for r in nr if r['season']==y]) for y in test_years},
                  'twoPartHurdle':{str(y):summarize([r for r in hr if r['season']==y]) for y in test_years}}}

def run():
    raw=pd.read_csv(RAW,low_memory=False)
    g=raw[(raw.game_type=='REG')&(raw.season>=2000)&(raw.season<=2025)].dropna(subset=['home_score','away_score']).copy()
    for c in ['home_score','away_score']: g[c]=g[c].astype(int)
    g['home_team']=g.home_team.astype(str).replace(ALIASES); g['away_team']=g.away_team.astype(str).replace(ALIASES)
    g=add_prior_context(g)
    # Select an intercept-only recency window on 2014-15; nothing later is consulted.
    val_law=fit_score_law(g,2013); val_train=g[(g.season>=2000)&(g.season<=2013)]; val=g[g.season.isin([2014,2015])]
    variant_scores={}
    for window in [None,3,5,10]:
        h=fit_hurdle(val_train,window or 14); p=predict_p(val,val_law,h)
        variant_scores['expanding' if window is None else f'trailing{window}']=event_metrics(val.shutout.astype(int),p)
    selected=min(variant_scores,key=lambda f:(variant_scores[f]['brier'],f))
    selected_window=None if selected=='expanding' else int(selected.replace('trailing',''))
    final_pre=evaluated(g,2015,[2016,2017],selected_window or 16)
    retrospective=evaluated(g,2017,list(range(2018,2026)),selected_window or 18,law_override=runtime_score_law())
    gameplay_law=fit_score_law(g,2017); gameplay_h=fit_hurdle(g[g.season<=2017],selected_window or 18)
    # Fit selected hurdle on all pre-cutoff scores for proposed runtime parameters.
    return {'version':'score-distribution-shutout-hurdle-v1','asOf':'2026-11-12',
      'protocol':{'formSelectionTrainSeasons':[2000,2013],'formSelectionValidationSeasons':[2014,2015],
       'finalPre2018TrainSeasons':[2000,2015],'finalPre2018TestSeasons':[2016,2017],
       'gameplayFitSeasons':[2000,2017],'retrospectiveKnownExposedTestSeasons':list(range(2018,2026)),
       'excludedIncompleteSeason':2026,'noPost2017Tuning':True},
      'data':{'source':'nflverse schedules/games.csv archived at data/raw/games.csv','sourceSha256':sha(RAW),
       'rowsBySeason':{str(y):int((g.season==y).sum()) for y in range(2000,2026)},
       'modelArtifactSha256':sha(MODEL)},
      'research':{'hurdleReference':{'citation':'Mullahy, J. (1986), Specification and testing of some modified count data models, Journal of Econometrics 33(3), 341–365.','url':'https://doi.org/10.1016/0304-4076(86)90002-3','relevance':'A two-part model separates threshold-crossing probability from the conditional positive distribution.'},
       'footballScoreReference':{'citation':'Baker, R. D. and McHale, I. G. (2013), Forecasting exact scores in National Football League games, International Journal of Forecasting 29(1), 122–130.','url':'https://doi.org/10.1016/j.ijforecast.2012.07.002','relevance':'NFL exact scores arise from multiple discrete scoring events; their paper models scoring as a point process.'},
       'probabilityEvaluationReference':{'citation':'Gneiting, T. and Raftery, A. E. (2007), Strictly Proper Scoring Rules, Prediction, and Estimation, JASA 102(477), 359–378.','url':'https://doi.org/10.1198/016214506000001437','relevance':'Use Brier/log loss for the shutout event and CRPS/interval coverage for predictive score distributions.'}},
      'boundedPlan':'Fit only intercept-only shutout rates with expanding, trailing-3, trailing-5, and trailing-10 season windows; select by validation Brier on 2014–15, evaluate once on 2016–17, then refit the selected rate window through 2017 for retrospective 2018–25. Positive-score law is existing correlated normal conditional on no shutout; shutout scorelines use that same law conditional on any team scoring zero. No engine edits, causal claim, or release threshold change.',
      'validationFormComparison':variant_scores,'selectedWindow':selected,
      'finalPre2018Test':final_pre,'retrospectiveKnownExposedTest':retrospective,
      'proposedGameplayParameters':{'fitThroughSeason':2017,'scoreLaw':runtime_score_law(),'shutoutHurdle':gameplay_h,'monteCarloDrawsPerObservedGameInAudit':N_FORECAST,'baseDrawsForConditionalSamplingInAudit':N_BASE,
       'conditionalScoreDistribution':'Current analytics/model.json correlated-normal margin/total draw and NFL score transform, conditioned on the fitted shutout branch. On the shutout branch, sample from baseline draws with either score zero; on the positive branch, sample from baseline draws with both scores positive. The hurdle probability chooses the branch.',
       'seedRecommendation':'keyed by seed, season, matchup, game type, component=shutout-hurdle or score-conditional'},
      'decision':'The three-season intercept-only hurdle wins 2014–15 Brier selection. On the 2016–17 final test its shutout Brier is slightly better but log loss is worse than the normal law; the exposed 2018–25 diagnostic improves shutout probability scores and lowers predicted shutouts toward observed frequency. Score-distribution gains are small/mixed, and this known-exposed diagnostic is not independent evidence. Keep it a candidate for review; no adoption claim.',
      'limitations':['Post-2017 outcomes have been inspected in prior project diagnostics; chronology prevents leakage but does not make them an untouched test.','2016–17 final pre-2018 evaluation has only two seasons and low shutout counts.','Conditional distributions inherit the existing normal score model and its limitations.','A fit to 2000–2017 assumes the shutout relationship is stable; future NFL scoring regimes may differ.','No causal draft effect or alternate-history truth is identified.']}


def write_report(r):
    lines=['# Shutout hurdle score distribution experiment','','## Protocol','',
      f"The shutout rate window was selected on 2014–15 (training through 2013): **{r['selectedWindow']}** by lowest Brier score. The frozen pre-2018 test is 2016–17 (fit through 2015). After that test, selected parameters are refit through 2017 for a known-exposed retrospective check on 2018–25. The 2026 season is incomplete and excluded.", '',
      'The candidate uses an intercept-only empirical shutout probability estimated from the selected pre-cutoff window. It then draws from the existing correlated normal score model conditional on that branch: zero scores for the shutout branch, two positive scores for the other branch. This makes an explicit, empirically estimated hurdle without clipping or forcing a desired shutout rate.', '',
      '## Hurdle form validation (2014–15)', '', '| Form | Brier | Log loss | Predicted rate | Observed rate |', '|---|---:|---:|---:|---:|']
    for k,v in r['validationFormComparison'].items(): lines.append(f"| {k} | {v['brier']:.5f} | {v['logLoss']:.5f} | {v['predictedRate']:.3%} | {v['observedRate']:.3%} |")
    for title,key in [('Frozen final pre-2018 test (2016–17)','finalPre2018Test'),('Known-exposed retrospective diagnostic (2018–25)','retrospectiveKnownExposedTest')]:
        lines += ['',f'## {title}','', '| Model | Games | Total MAE | Margin MAE | Total CRPS | Margin CRPS | Shutout Brier | Predicted / observed shutouts | 90% total coverage | 90% margin coverage |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for model,v in r[key]['scoreMetrics'].items():
            lines.append(f"| {model} | {v['games']} | {v['totalMAE']:.3f} | {v['marginMAE']:.3f} | {v['totalCRPS']:.3f} | {v['marginCRPS']:.3f} | {v['shutoutBrier']:.5f} | {v['predictedShutoutRate']:.3%} / {v['observedShutoutRate']:.3%} | {v['total90Coverage']:.1%} | {v['margin90Coverage']:.1%} |")
        ev=r[key]['eventForecastMetrics']; lines += ['',f"Shutout probability-only Brier: {ev['brier']:.5f}; log loss: {ev['logLoss']:.5f}."]
    lines += ['', '## Gameplay parameters','',
      'The proposed runtime parameters are recorded in `score_distribution.json`: the current score-law parameters fitted through 2017 plus a shutout rate of 2.083% estimated from 2015–17. Sampling uses one keyed Bernoulli shutout decision, then draws from the current bivariate normal score law conditional on the selected branch. In exact engine form, reject and redraw score-law samples until either one team scores zero (shutout branch) or both score positive (non-shutout branch). The evaluation uses Monte Carlo draws; no runtime changes are included here.', '',
      '## Decision and limits','',r['decision'],'',
      'NFL score forecasting research models scoring events because multiple football scoring outcomes produce a discrete score distribution ([Baker & McHale, 2013](https://doi.org/10.1016/j.ijforecast.2012.07.002)). Two-part count models separate threshold probability from the conditional positive distribution ([Mullahy, 1986](https://doi.org/10.1016/0304-4076(86)90002-3)). Proper scoring rules support evaluating event probabilities with Brier/log loss and outcome distributions with CRPS and interval coverage ([Gneiting & Raftery, 2007](https://doi.org/10.1198/016214506000001437)).', '',
      'The post-2017 results are retrospective because they have already been examined elsewhere in this project. The final pre-2018 test contains only two seasons and 14 shutouts. In 2018–25, the source has 2,127 regular-season games because the 2022 Bills–Bengals game was canceled and not replayed. Neither test proves future calibration, causality, or alternate-history accuracy. No release threshold was changed.']
    (A/'score_distribution.md').write_text('\n'.join(lines)+'\n')

def main():
    r=run(); (A/'score_distribution.json').write_text(json.dumps(r,indent=2)+'\n'); write_report(r)
    print(json.dumps({'selected':r['selectedWindow'],'validation':r['validationFormComparison'],'pre2018':r['finalPre2018Test']['scoreMetrics'],'2018_25':r['retrospectiveKnownExposedTest']['scoreMetrics']},indent=2))
if __name__=='__main__': main()
