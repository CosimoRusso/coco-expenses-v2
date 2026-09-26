import { describe, it, expect } from 'vitest'

import type { Movement } from '@/interfaces/Balance'
import { formatMovement, movementClass } from '../movements'

function movement(amount: string): Movement {
  return {
    description: 'Dinner',
    date: '2026-09-26',
    amount,
    currency: { id: 1, code: 'EUR', symbol: '€', display_name: 'Euro' },
  }
}

describe('formatMovement', () => {
  it('shows what the person owes the user with a plus', () => {
    expect(formatMovement(movement('15.5'))).toBe('+ € 15.50')
  })

  it('shows what the user owes the person with a minus', () => {
    expect(formatMovement(movement('-5.00'))).toBe('− € 5.00')
  })
})

describe('movementClass', () => {
  it('marks what the user owes as an error', () => {
    expect(movementClass(movement('-0.01'))).toBe('text-error')
  })

  it('marks a zero quota as a success', () => {
    expect(movementClass(movement('0.00'))).toBe('text-success')
  })
})
