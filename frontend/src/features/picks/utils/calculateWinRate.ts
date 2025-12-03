export function calculateWinRate(wins: number, losses: number): number {
  const total = wins + losses
  if (total === 0) return 0
  return (wins / total) * 100
}

