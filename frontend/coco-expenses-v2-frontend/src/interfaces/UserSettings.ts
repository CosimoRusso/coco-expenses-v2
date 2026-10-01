export interface UserSettings {
  id: number
  user_id: number
  active_trip: number | null
  preferred_currency: number | null
  default_statistics_start_date: string | null
  default_statistics_end_date: string | null
  statistics_start_date: string
  statistics_end_date: string
}
