export interface SharedExpenseParticipant {
  // Id of the participant, matched by Expense.shared_expense_participant
  id: number
  user_id: number
  first_name: string
  last_name: string
  quota: string
}

export interface SharedExpenseSummary {
  id: number
  total_amount: string
  currency: number
  // User id of the creator, who cannot be removed from the shared expense
  created_by: number
  participants: SharedExpenseParticipant[]
}
