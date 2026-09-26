import { describe, it, expect } from 'vitest'

import { remainingCents, splitEqually, splitError } from '../split'

describe('splitEqually', () => {
  it('gives the leftover cent to the creator, first', () => {
    expect(splitEqually(10, [7, 8, 9])).toEqual({ 7: '3.34', 8: '3.33', 9: '3.33' })
  })

  it('splits an exact division in equal quotas', () => {
    expect(splitEqually(22.56, [1, 2])).toEqual({ 1: '11.28', 2: '11.28' })
  })
})

describe('remainingCents', () => {
  it('counts a missing quota as zero', () => {
    expect(remainingCents(10, { 1: 6.5 }, [1, 2])).toBe(350)
  })

  it('is negative when the quotas exceed the total', () => {
    expect(remainingCents(10, { 1: '6.00', 2: '4.01' }, [1, 2])).toBe(-1)
  })

  it('ignores quotas of people no longer sharing', () => {
    expect(remainingCents(10, { 1: 6, 2: 4, 3: 5 }, [1, 2])).toBe(0)
  })
})

describe('splitError', () => {
  it('accepts quotas adding up to the total', () => {
    expect(splitError(22.56, { 1: 10, 2: 8, 3: 4.56 }, [1, 2, 3])).toBe('')
  })

  it('accepts a zero quota for a friend', () => {
    expect(splitError(10, { 1: 10, 2: 0 }, [1, 2])).toBe('')
  })

  it('tells how much is left to assign', () => {
    expect(splitError(22.56, { 1: 10, 2: 8, 3: 1.56 }, [1, 2, 3])).toBe('3.00 left to assign')
  })

  it('tells how much the quotas exceed the total', () => {
    expect(splitError(10, { 1: 6, 2: 4.5 }, [1, 2])).toBe('0.50 over the total')
  })

  it('rejects a negative quota', () => {
    expect(splitError(10, { 1: 11, 2: -1 }, [1, 2])).toBe('A quota cannot be negative')
  })

  it('accepts a zero quota for the creator, who paid for the others', () => {
    expect(splitError(10, { 1: 0, 2: 10 }, [1, 2])).toBe('')
  })
})
