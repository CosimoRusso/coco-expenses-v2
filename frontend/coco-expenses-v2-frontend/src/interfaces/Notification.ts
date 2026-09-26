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
