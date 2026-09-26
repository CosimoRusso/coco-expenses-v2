export interface SharedExpenseRequest {
  // Id of the current user's SharedExpenseParticipant
  id: number
  quota: string
  description: string
  total_amount: string
  currency: number
  created_by: string
  is_completed: boolean
}

export interface Notification {
  id: number
  kind: string
  read_at: string | null
  created_at: string
  shared_expense: SharedExpenseRequest | null
}
