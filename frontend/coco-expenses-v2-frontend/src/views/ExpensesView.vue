<script setup lang="ts">
import ExpensesList from '@/components/ExpensesList.vue'
import ExpenseForm from '@/components/ExpenseForm.vue'
import { ref, onMounted, watch } from 'vue'
import apiFetch from '@/utils/apiFetch'
import type { ExpenseCategory } from '@/interfaces/ExpenseCategory'
import type { Currency } from '@/interfaces/Currency'
import type { Trip } from '@/interfaces/Trip'
import type { UserSettings } from '@/interfaces/UserSettings'
import type { Expense } from '@/interfaces/Expense'
import type { PaginatedResponse } from '@/interfaces/PaginatedResponse'

const initialPageLoading = ref(true)
const expenses = ref<Expense[]>([])
const categories = ref<ExpenseCategory[]>([])
const trips = ref<Trip[]>([])
const currencies = ref<Currency[]>([])
const userSettings = ref<UserSettings | null>(null)
const tableErrors = ref<string[]>([])

// Pagination state
const currentPage = ref(1)
const totalCount = ref(0)
const hasNextPage = ref(false)
const hasPreviousPage = ref(false)

// Filter state
const filterCategory = ref<number | null>(null)
const filterTrip = ref<number | null>(null)
const filterIsExpense = ref<boolean | null>(null)
const filterStartDate = ref<string | null>(null)
const filterEndDate = ref<string | null>(null)

// Editing state
const editingExpense = ref<Expense | null>(null)

onMounted(async () => {
  initialPageLoading.value = true
  try {
    await fetchMetadata()
  } finally {
    initialPageLoading.value = false
  }
})

async function fetchMetadata() {
  await Promise.all([
    fetchCategories(),
    fetchTrips(),
    fetchExpenses(),
    fetchCurrencies(),
    fetchUserSettings(),
  ])
}

// Fetch expenses
async function fetchExpenses() {
  try {
    let url = '/expenses/expenses/'
    const params: string[] = []

    if (filterIsExpense.value !== null) {
      params.push(`is_expense=${filterIsExpense.value}`)
    }
    if (filterCategory.value !== null) {
      params.push(`category=${filterCategory.value}`)
    }
    if (filterTrip.value !== null) {
      params.push(`trip=${filterTrip.value}`)
    }
    if (filterStartDate.value !== null && filterStartDate.value !== '') {
      params.push(`start_date=${filterStartDate.value}`)
    }
    if (filterEndDate.value !== null && filterEndDate.value !== '') {
      params.push(`end_date=${filterEndDate.value}`)
    }
    // Add page parameter
    params.push(`page=${currentPage.value}`)

    if (params.length > 0) {
      url += `?${params.join('&')}`
    }

    const response = await apiFetch(url)
    if (response.ok) {
      const data: PaginatedResponse<Expense> = await response.json()
      expenses.value = data.results
      totalCount.value = data.count
      hasNextPage.value = data.next !== null
      hasPreviousPage.value = data.previous !== null
    } else {
      throw new Error('Failed to load expenses.')
    }
  } catch (error) {
    console.error('Error fetching expenses:', error)
    tableErrors.value.push('Failed to load categories.')
  }
}

async function fetchCurrencies() {
  try {
    const response = await apiFetch('/expenses/currencies/')
    if (response.ok) {
      currencies.value = await response.json()
    } else {
      throw new Error('Failed to load currencies.')
    }
  } catch (error) {
    console.error('Error fetching currencies:', error)
    tableErrors.value.push('Failed to load currencies.')
  }
}

async function fetchCategories() {
  try {
    const response = await apiFetch('/expenses/expense-categories')
    if (response.ok) {
      categories.value = await response.json()
    } else {
      throw new Error('Failed to load categories.')
    }
  } catch (error) {
    console.error('Error fetching categories:', error)
    tableErrors.value.push('Failed to load categories.')
  }
}

async function fetchUserSettings() {
  try {
    const response = await apiFetch('/expenses/user-settings/self/')
    if (response.ok) {
      userSettings.value = await response.json()
    } else {
      throw new Error('Failed to load user settings.')
    }
  } catch (error) {
    console.error('Error fetching user settings:', error)
    tableErrors.value.push('Failed to load user settings.')
  }
}

async function fetchTrips() {
  try {
    const response = await apiFetch('/expenses/trips/')
    if (response.ok) {
      trips.value = await response.json()
    } else {
      throw new Error('Failed to load trips.')
    }
  } catch (error) {
    console.error('Error fetching trips:', error)
    tableErrors.value.push('Errore durante il caricamento dei viaggi.')
  }
}

function onExpenseAdded(expense: Expense) {
  // Simply add them as first element of the current page, when the user refreshes the page everything will work just fine
  expenses.value.unshift(expense)
}

function onExpenseUpdated(expense: Expense) {
  // Update the expense in the list
  const index = expenses.value.findIndex((e) => e.id === expense.id)
  if (index !== -1) {
    expenses.value[index] = expense
  }
  editingExpense.value = null
}

function onExpenseDeleted(expenseId: number) {
  expenses.value = expenses.value.filter((e) => e.id !== expenseId)
}

function onEditExpense(expense: Expense) {
  editingExpense.value = expense
}

function onPageChanged(page: number) {
  currentPage.value = page
  fetchExpenses()
}

// Reset to page 1 when filters change and reload
watch([filterCategory, filterTrip, filterIsExpense, filterStartDate, filterEndDate], () => {
  if (currentPage.value !== 1) {
    currentPage.value = 1
  }
  // Fetch expenses with updated filters and page 1
  fetchExpenses()
})
</script>

<template>
  <div v-if="!initialPageLoading">
    <ExpenseForm
      :initialPageLoading="initialPageLoading"
      :categories="categories"
      :trips="trips"
      :currencies="currencies"
      :userSettings="userSettings"
      :editingExpense="editingExpense"
      @expense-added="onExpenseAdded"
      @expense-updated="onExpenseUpdated"
    />
    <ExpensesList
      :initialPageLoading="initialPageLoading"
      :categories="categories"
      :trips="trips"
      :currencies="currencies"
      :userSettings="userSettings"
      :expenses="expenses"
      :currentPage="currentPage"
      :totalCount="totalCount"
      :hasNextPage="hasNextPage"
      :hasPreviousPage="hasPreviousPage"
      @expense-deleted="onExpenseDeleted"
      @reload-expenses="fetchExpenses"
      @page-changed="onPageChanged"
      @edit-expense="onEditExpense"
      v-model:filter-category="filterCategory"
      v-model:filter-trip="filterTrip"
      v-model:filter-is-expense="filterIsExpense"
      v-model:filter-start-date="filterStartDate"
      v-model:filter-end-date="filterEndDate"
    />
  </div>
  <div v-else-if="tableErrors.length > 0">
    <p>{{ tableErrors.join('\n') }}</p>
  </div>
  <div v-else>
    <p>Loading...</p>
  </div>
</template>

<style scoped></style>
