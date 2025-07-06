function dateToISOString(date: Date): string {
  return date.toISOString().substring(0, 10) // Returns date in YYYY-MM-DD format
}

function dateFromIsoString(dateString: string | null): Date | null {
  if (!dateString) {
    return null
  }
  return new Date(dateString) // Converts YYYY-MM-DD string to Date object
}

export { dateToISOString, dateFromIsoString }
