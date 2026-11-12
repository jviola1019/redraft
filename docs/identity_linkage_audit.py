"""Within-source uniqueness diagnostics; NOT human recognition or a population anonymity guarantee."""
import collections,hashlib,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=ROOT/'data/processed/scenario-2018.json';blob=p.read_bytes();data=json.loads(blob)
rows=[p for p in data['prospects'] if p.get('eligibilitySource')=='combine-participant']
fields=['heightIn','weightLb','forty','bench','verticalIn','broadJumpIn','cone','shuttle']
cases={'position_only':['position'],'college_position':['college','position'],'college_position_height_weight':['college','position','heightIn','weightLb'],'position_exact_measurements':['position']+fields}
results=[]
for name,keys in cases.items():
 counts=collections.Counter(tuple(p.get(k) for k in keys) for p in rows)
 sizes=[counts[tuple(p.get(k) for k in keys)] for p in rows]
 results.append({'profile':name,'fields':keys,'records':len(rows),'uniqueRecords':sum(n==1 for n in sizes),'uniqueFraction':sum(n==1 for n in sizes)/len(rows),'minimumEquivalenceClass':min(sizes),'medianRecordEquivalenceClass':statistics.median(sizes),'note':'Exact equality including nulls; null patterns may contribute to uniqueness.'})
out={'datasetVersion':data['metadata'].get('version'),'datasetSha256':hashlib.sha256(blob).hexdigest(),'population':'336 documented combine participants only; not complete eligible NFL population','diagnostics':results,'interpretation':'Within-source quasi-identifier uniqueness, not actual human recognition accuracy. Exact public profiles can be linked if an external reference maps these fields to names. Coarsened runtime DTO must be audited separately.','humanStudy':'not executed'}
(ROOT/'docs/identity_linkage_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(results,indent=2))
