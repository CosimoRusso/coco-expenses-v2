export interface RecurringExpense {
  id?: number
  start_date: string
  end_date: string | null
  amount: number
  category: number | null
  trip: number | null
  schedule: string
  description: string
  is_expense: boolean
  currency: number | null
  amortization_duration?: number
  amortization_unit?: 'DAY' | 'WEEK' | 'MONTH' | 'YEAR'
}
