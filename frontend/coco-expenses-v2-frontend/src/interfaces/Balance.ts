import type { Currency } from '@/interfaces/Currency'

export interface Movement {
  description: string
  date: string
  // Positive when the person owes the current user their quota, negative when the user owes theirs
  amount: string
  currency: Currency
}

export interface Balance {
  user_id: number
  first_name: string
  last_name: string
  // Positive when the person owes the current user, negative when the user owes them
  amount: string
  // The latest shared expenses with the person, newest first
  movements: Movement[]
}

export interface Balances {
  currency: Currency
  balances: Balance[]
}

export interface MovementsPage {
  count: number
  next: string | null
  previous: string | null
  results: Movement[]
}
