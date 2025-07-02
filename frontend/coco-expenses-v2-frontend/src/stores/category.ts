import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ExpenseCategory } from '@/interfaces/ExpenseCategory.ts'
import { CategoryError } from '@/errors/category.ts'

export const useCategoryStore = defineStore('category', () => {
  const categories = ref<ExpenseCategory[]>([])

  async function fetchCategories() {
    const response = await fetch('/api/expenses/categories')
    if (!response.ok) {
      throw new CategoryError('Failed to fetch categories')
    }
    categories.value = await response.json()
  }

  return {
    categories,
    fetchCategories,
  }
})
