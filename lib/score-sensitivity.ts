import type {ScoreComponent} from './types';

export function decisionScoreSensitivity(officialScore: number, components?: readonly ScoreComponent[] | null) {
  if (!Array.isArray(components) || !components.length || components.some(c =>
    !c || !Number.isFinite(c.score) || c.score < 0 || c.score > 100 ||
    !Number.isFinite(c.weight) || c.weight < 0
  )) return null;

  const total = components.reduce((sum, c) => sum + c.weight, 0);
  const baseline = components.reduce((sum, c) => sum + c.score * c.weight, 0);
  if (Math.abs(total - 1) > 1e-9 || Math.round(baseline) !== officialScore) return null;

  // Use the same one-at-a-time perturbations and integer rounding as the rank audit.
  const scores = components.flatMap((_, index) => [0.5, 1.5].map(scale => {
    const weights = components.map((c, i) => c.weight * (i === index ? scale : 1));
    const sum = weights.reduce((n, w) => n + w, 0);
    return Math.round(components.reduce((n, c, i) => n + c.score * (weights[i] / sum), 0));
  }));

  return {low: Math.min(officialScore, ...scores), high: Math.max(officialScore, ...scores)};
}
