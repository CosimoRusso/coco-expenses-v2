// Values to prefill when completing a share
export interface ShareSuggestion {
  // The category the user usually gives to this friend's expenses of the same kind
  category: number | null
  // The dates of the creator's own expense
  expense_date: string | null
  amortization_start_date: string | null
  amortization_end_date: string | null
}

export interface SharedExpenseRequest {
  // Id of the current user's SharedExpenseParticipant
  id: number
  quota: string
  description: string
  total_amount: string
  currency: number
  created_by: string
  is_completed: boolean
  expense_id: number | null
  // Null once the share is completed
  suggestion: ShareSuggestion | null
}

export interface SharedExpenseModification {
  description: string
  modified_by: string
  amount_before: string
  currency_before: number
  amount_after: string
  currency_after: number
  number_participants_before: number
  number_participants_after: number
  you_were_added: boolean
  you_were_removed: boolean
}

export interface SharedExpenseDeletion {
  deleted_by: string
  description: string
  amount: string
  currency: number
}

export interface Notification {
  id: number
  kind: string
  read_at: string | null
  created_at: string
  shared_expense: SharedExpenseRequest | null
  modification: SharedExpenseModification | null
  deletion: SharedExpenseDeletion | null
}
