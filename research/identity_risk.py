"""Descriptive re-identification risk, not a formal anonymity guarantee."""
from pathlib import Path
import json,collections,math
ROOT=Path(__file__).resolve().parents[1]
def band(x,width):return None if x is None else math.floor(x/width)*width
def audit(ps,fields,fn=None):
 groups=collections.Counter(tuple((fn(k,p[k]) if fn else p[k]) for k in fields) for p in ps)
 counts=[groups[tuple((fn(k,p[k]) if fn else p[k]) for k in fields)] for p in ps]
 return {'fields':fields,'groups':len(groups),'singletonProspects':sum(n==1 for n in counts),'singletonFraction':sum(n==1 for n in counts)/len(ps),'fewerThanFiveMatches':sum(n<5 for n in counts),'medianMatchingCandidates':sorted(counts)[len(counts)//2],'smallestGroup':min(counts),'largestGroup':max(counts)}
def main():
 d=json.loads((ROOT/'data/processed/scenario-2018.json').read_text());ps=[p for p in d['prospects'] if p['eligibilitySource']=='combine-participant'];measurements=['heightIn','weightLb','forty','bench','verticalIn','broadJumpIn','cone','shuttle']
 comparisons={
 'positionOnly':audit(ps,['position']),
 'collegeOnly':audit(ps,['college']),
 'collegePosition':audit(ps,['position','college']),
 'positionExactBody':audit(ps,['position','heightIn','weightLb']),
 'positionExactMeasurements':audit(ps,['position']+measurements),
 'positionCoarseBody':audit(ps,['position','heightIn','weightLb'],lambda k,x:band(x,3) if k=='heightIn' else band(x,20) if k=='weightLb' else x),
 'positionCoarseBodySpeed':audit(ps,['position','heightIn','weightLb','forty'],lambda k,x:band(x,3) if k=='heightIn' else band(x,20) if k=='weightLb' else band(x,.2) if k=='forty' else x)
 }
 bypos=[]
 for pos in sorted({p['position'] for p in ps}):
  subset=[p for p in ps if p['position']==pos];a=audit(subset,['college']);bypos.append({'position':pos,'prospects':len(subset),'collegeSingletons':a['singletonProspects'],'fraction':a['singletonFraction']})
 report={'verifiedDate':'2026-11-02','population':'336 combine participants only','method':'Exact equivalence classes of displayed field tuples in the downloaded2018 cohort. Nulls are explicit values. No external attacker model or privacy guarantee.','comparisons':comparisons,'collegePositionByPosition':bypos,'interpretation':['College plus position often uniquely identifies a real prospect within this cohort.','Hiding names alone is not anonymity. Hiding college reduces an easy recognition clue but exact measurements still frequently identify athletes.','Use per-run opaque browser IDs; canonical stable hashes derived from names and college can be dictionary-matched if exposed.','Coarsen or withhold information explicitly instead of fabricating statistics.','Measure inference utility separately; fewer singleton groups does not establish player recognition is impossible.','Specific target-model probabilities or position rarity can remain identifying.']} 
 (ROOT/'data/clean/identity_risk_2018.json').write_text(json.dumps(report,indent=2));print(json.dumps(comparisons,indent=2))
if __name__=='__main__':main()
