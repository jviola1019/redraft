import type { GameState, ReplicateResult } from '@/lib/types';

const workloadValue = (value: number | undefined) =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;

export function playerDevelopment(
  game: Pick<GameState, 'year' | 'team' | 'selections'>,
  runs: ReplicateResult[],
  identitiesRevealed: boolean,
) {
  // The featured run retains player seasons; compacted runs cannot supply an ensemble player average.
  if (!identitiesRevealed) return [];
  const seasons = runs.find(run => run.index === 0)?.alternate.seasons ?? [];
  return game.selections
    .filter(pick => pick.team === game.team)
    .sort((a, b) => a.overall - b.overall)
    .map(pick => ({
      pick,
      seasons: Array.from({ length: 5 }, (_, index) => {
        const year = game.year + index;
        const season = seasons.find(season => season.year === year);
        const player = season?.players?.find(player => player.prospectId === pick.prospectId && player.team === game.team && player.season === year);
        const team = season?.teams.find(team => team.team === game.team);
        const teamGames = team ? team.wins + team.losses + team.ties : 0;
        const starts = workloadValue(player?.starts);
        return {
          year,
          games: workloadValue(player?.games),
          starts,
          startShare: starts !== null && teamGames > 0 && starts <= teamGames ? starts / teamGames : null,
          contribution: workloadValue(player?.contribution),
        };
      }),
    }));
}
