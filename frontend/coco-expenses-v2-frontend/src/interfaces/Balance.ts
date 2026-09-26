import type { Currency } from '@/interfaces/Currency'

export interface Balance {
  user_id: number
  first_name: string
  last_name: string
  // Positive when the person owes the current user, negative when the user owes them
  amount: string
}

export interface Balances {
  currency: Currency
  balances: Balance[]
}
