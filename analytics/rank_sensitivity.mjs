/** Match public integer scores; use average ranks for tied-rank Spearman. */
export function rankedScores(rows, round = true) {
  const sorted = rows.map(row => ({...row, rawScore:row.score, score:round ? Math.round(row.score) : row.score}))
    .sort((a,b)=>b.score-a.score || a.name.localeCompare(b.name));
  for (let start=0;start<sorted.length;) {
    let end=start+1;
    while (end<sorted.length && sorted[end].score===sorted[start].score) end++;
    for(let i=start;i<end;i++) {
      sorted[i].sharedRank=start+1;
      sorted[i].averageRank=(start+1+end)/2;
    }
    start=end;
  }
  return sorted;
}

export function compareRanks(baseline, candidate) {
  const names=baseline.map(r=>r.name);
  if (new Set(names).size!==names.length || candidate.length!==names.length || new Set(candidate.map(r=>r.name)).size!==candidate.length ||
      candidate.some(r=>!names.includes(r.name))) throw Error('Rank comparison requires identical unique policies.');
  const x=baseline.map(r=>r.averageRank);
  const y=names.map(n=>candidate.find(r=>r.name===n).averageRank);
  const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
  const mx=mean(x),my=mean(y);
  const xx=x.reduce((s,v)=>s+(v-mx)**2,0),yy=y.reduce((s,v)=>s+(v-my)**2,0);
  const covariance=x.reduce((s,v,i)=>s+(v-mx)*(y[i]-my),0);
  const top=rows=>rows.filter(r=>r.sharedRank===1).map(r=>r.name).sort();
  return {spearmanToDefault:xx>0&&yy>0?covariance/Math.sqrt(xx*yy):null,
    topPolicyChanged:JSON.stringify(top(baseline))!==JSON.stringify(top(candidate)),
    topPolicySet:top(candidate),
    allScoresTied:yy===0};
}

export function rankCorrelationSummary(comparisons) {
  const values=comparisons.map(row=>row.spearmanToDefault).filter(Number.isFinite);
  return {minRankCorrelation:values.length?Math.min(...values):null,
    rankCorrelationStatus:values.length?'available':'undefined-no-rank-variance',
    undefinedRankComparisons:comparisons.length-values.length};
}
