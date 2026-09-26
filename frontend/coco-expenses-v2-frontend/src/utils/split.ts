// Amounts are handled in cents, so that quotas add up exactly to the total

export type SplitMode = 'equally' | 'amount'

// Quotas by user id, in the currency's units as typed in the inputs
export type Quotas = Record<number, number | string | null | undefined>

export function toCents(amount: number | string | null | undefined): number {
  return Math.round(Number(amount || 0) * 100)
}

export function fromCents(cents: number): string {
  return (cents / 100).toFixed(2)
}

/**
 * Quotas splitting `total` equally between `userIds`, the same way the backend does:
 * the first user, the creator, takes the leftover cents.
 */
export function splitEqually(total: number, userIds: number[]): Record<number, string> {
  const totalCents = toCents(total)
  const baseCents = Math.floor(totalCents / userIds.length)
  const leftoverCents = totalCents - baseCents * userIds.length
  return Object.fromEntries(
    userIds.map((userId, index) => [userId, fromCents(baseCents + (index ? 0 : leftoverCents))]),
  )
}

/** Cents of `total` not yet given to any of `userIds`; negative when the quotas exceed it. */
export function remainingCents(total: number, quotas: Quotas, userIds: number[]): number {
  const assignedCents = userIds.reduce((sum, userId) => sum + toCents(quotas[userId]), 0)
  return toCents(total) - assignedCents
}

/** Why the quotas cannot be saved, or '' when they can. */
export function splitError(total: number, quotas: Quotas, userIds: number[]): string {
  const remaining = remainingCents(total, quotas, userIds)
  if (remaining > 0) return `${fromCents(remaining)} left to assign`
  if (remaining < 0) return `${fromCents(-remaining)} over the total`
  if (userIds.some((userId) => toCents(quotas[userId]) < 0)) return 'A quota cannot be negative'
  return ''
}
