export type DefaultStatisticsMethod = 'HARDCODED_DATES' | 'DAYS_AGO'

export interface UserSettings {
  id: number
  user_id: number
  active_trip: number | null
  preferred_currency: number | null
  is_encrypted: boolean
  default_statistics_method: DefaultStatisticsMethod
  default_statistics_start_date: string | null
  default_statistics_end_date: string | null
  default_statistics_n_days_ago_from: number | null
  default_statistics_n_days_ago_to: number | null
  statistics_start_date: string
  statistics_end_date: string
}
