from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];A=R/'analytics';O=A/'figures';O.mkdir(exist_ok=True)
m=json.loads((A/'model.json').read_text());plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False});green='#176653';orange='#c0582a'
bins=m['prospect']['selectedTestMetrics']['reliability'];fig,axs=plt.subplots(1,2,figsize=(11,4.3),layout='constrained');axs[0].plot([0,1],[0,1],'--',c='#aaa');axs[0].plot([b['predicted'] for b in bins],[b['observed'] for b in bins],'-o',c=green)
for b in bins:axs[0].annotate(str(b['n']),(b['predicted'],b['observed']),xytext=(0,7),textcoords='offset points',fontsize=8)
axs[0].set(xlabel='Predicted rookie-role probability',ylabel='Observed ≥200-snap rate',title='Reliability · labels show bin N',xlim=(0,.85),ylim=(0,.85));rows=[r for r in m['prospect']['subgroupTestMetrics'] if r['group']=='position'];axs[1].bar([r['value'] for r in rows],[r['brier'] for r in rows],color=orange);axs[1].set(ylabel='Held-out Brier score',title='Performance varies by position');fig.suptitle('REDRAFT · held-out 2016–2017 rookie participation, not career validation');fig.savefig(O/'rookie_calibration.png',dpi=170);plt.close(fig)
p=pd.read_csv(A/'outcomes/team_test_predictions.csv');fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained');axs[0].scatter(p.prediction,p.margin,alpha=.2,s=15,c=green);axs[0].plot([-20,20],[-20,20],'--',c='#aaa');axs[0].set(xlabel='Predicted margin',ylabel='Recorded margin',title='Game-margin test · 2016–2017');axs[1].hist(p.margin-p.prediction,bins=25,color=orange,edgecolor='white');axs[1].set(xlabel='Observed − predicted margin',ylabel='Games',title='Wide residual uncertainty');fig.savefig(O/'game_margin_validation.png',dpi=170);plt.close(fig)
c=json.loads((A/'coarsening_comparison.json').read_text());keys=list(c['comparisonsVsRaw']);labels=['Coarse measurements','10-point probability bands','Coarse + probability bands'];v=[c['comparisonsVsRaw'][k] for k in keys];means=[x['brierDifference'] for x in v];lo=[x['brierDifference']-x['withinCohortBootstrap95'][0] for x in v];hi=[x['withinCohortBootstrap95'][1]-x['brierDifference'] for x in v];fig,ax=plt.subplots(figsize=(8.3,4),layout='constrained');ax.axvline(0,c='#aaa',ls='--');ax.errorbar(means,range(3),xerr=[lo,hi],fmt='o',capsize=5,c=green);ax.set_yticks(range(3),labels);ax.invert_yaxis();ax.set(xlabel='Brier difference versus raw model · positive = worse',title='Candidate coarsening: measured information loss');ax.set_title('Candidate coarsening: measured information loss\nWithin-cohort bootstrap 95% intervals · not an equivalence or anonymity test',fontsize=11);fig.savefig(O/'coarsening_tradeoff.png',dpi=180);plt.close(fig)
path=A/'simulation_diagnostics.json'
if path.exists():
 d=json.loads(path.read_text());keys=['totalScoreMean','totalScoreSd','marginSd','teamWinSd'];labels=['Mean total points','SD total points','SD margin','SD team wins'];fig,axs=plt.subplots(1,4,figsize=(12,3.8),layout='constrained')
 for ax,k,label in zip(axs,keys,labels):
  s=d['simulatedBaseline'][k];ax.errorbar([0],[s['mean']],yerr=[[s['mean']-s['p025']],[s['p975']-s['mean']]],fmt='o',capsize=5,c=green);ax.scatter([.5],[d['observed2018Through2022'][k]],marker='D',c=orange);ax.set_xticks([0,.5],['Simulated','Recorded']);ax.set_title(label,fontsize=10)
 fig.suptitle('2018–2022 distributions · intervals across 256 simulated baselines');fig.savefig(O/'simulation_distributions.png',dpi=170);plt.close(fig)
print('Diagnostic figures rendered.')
