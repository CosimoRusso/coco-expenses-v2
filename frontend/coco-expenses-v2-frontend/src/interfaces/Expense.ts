export interface Expense {
    id?: number
    expense_date: string
    description: string
    amount: number
    amortization_start_date: string
    amortization_end_date: string
    category: number | null
    trip: number | null
    is_expense: boolean
    currency: number | null
  }