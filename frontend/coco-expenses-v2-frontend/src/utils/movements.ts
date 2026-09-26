import type { Movement } from '@/interfaces/Balance'

function formatMovement(movement: Movement): string {
  const amount = Number(movement.amount)
  const sign = amount < 0 ? '−' : '+'
  return `${sign} ${movement.currency.symbol} ${Math.abs(amount).toFixed(2)}`
}

function movementClass(movement: Movement): string {
  return Number(movement.amount) < 0 ? 'text-error' : 'text-success'
}

export { formatMovement, movementClass }
