class CategoryError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'CategoryError'
  }
}

export { CategoryError }
