import { describe, it, expect } from 'vitest'

import { activeBadgeClass, activeBorderClass, activeLabel, activeRowClass } from '../activeStatus'

describe('activeRowClass', () => {
  it('tints an active row green', () => {
    expect(activeRowClass(true)).toBe('bg-success/10')
  })

  it('greys out an inactive row', () => {
    expect(activeRowClass(false)).toBe('bg-base-200 text-base-content/50')
  })
})

describe('activeBorderClass', () => {
  it('marks an active row with a green edge', () => {
    expect(activeBorderClass(true)).toBe('border-l-success')
  })

  it('marks an inactive row with a grey edge', () => {
    expect(activeBorderClass(false)).toBe('border-l-base-300')
  })
})

describe('activeBadgeClass', () => {
  it('gives an active row a green badge', () => {
    expect(activeBadgeClass(true)).toBe('badge-success')
  })

  it('gives an inactive row a neutral badge', () => {
    expect(activeBadgeClass(false)).toBe('badge-neutral')
  })
})

describe('activeLabel', () => {
  it('labels an active row', () => {
    expect(activeLabel(true)).toBe('Active')
  })

  it('labels an inactive row', () => {
    expect(activeLabel(false)).toBe('Inactive')
  })
})
