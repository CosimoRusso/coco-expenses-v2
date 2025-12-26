<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DeleteIcon from '../../icons/DeleteIcon.vue'
import apiFetch from '@/utils/apiFetch'

import type { Expense } from '@/interfaces/Expense'
import type { ExpenseCategory } from '@/interfaces/ExpenseCategory'
import type { Currency } from '@/interfaces/Currency'
import type { Trip } from '@/interfaces/Trip'
import type { UserSettings } from '@/interfaces/UserSettings'

// Constants
const todayStr = new Date().toISOString().substring(0, 10)

// Data
const expenses = ref<Expense[]>([])
const categories = ref<ExpenseCategory[]>([])
const trips = ref<Trip[]>([])
const currencies = ref<Currency[]>([])
const userSettings = ref<UserSettings | null>(null)

const initialPageLoading = ref(true)
// New expense form
const newExpense = ref<Expense>({
  expense_date: todayStr,
  description: '',
  amount: 0,
  amortization_start_date: todayStr,
  amortization_end_date: todayStr,
  category: null,
  trip: null,
  is_expense: true,
  currency: null,
})

// Form error handling
const formError = ref('')
const tableErrors = ref<string[]>([])
const isSubmitting = ref(false)

// Fetch expenses
async function fetchExpenses() {
  try {
    const response = await apiFetch('/expenses/expenses/')
    if (response.ok) {
      expenses.value = await response.json()
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
    const response = await apiFetch('/expenses/expense-categories/')
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
// Add new expense
const addExpense = async () => {
  isSubmitting.value = true
  formError.value = ''

  try {
    // Validate form
    if (!newExpense.value.expense_date) {
      formError.value = 'Expense date is required'
      return
    }
    if (!newExpense.value.description) {
      formError.value = 'Description is required'
      return
    }
    if (!newExpense.value.category) {
      formError.value = 'Category is required'
      return
    }
    if (!newExpense.value.amortization_start_date || !newExpense.value.amortization_end_date) {
      formError.value = 'Amortization dates are required'
      return
    }

    const _selectedCategory = categories.value.find((c) => c.id === newExpense.value.category)
    if (!_selectedCategory) {
      formError.value = 'Invalid category selected'
      return
    }
    newExpense.value.is_expense = _selectedCategory.for_expense

    // Submit form
    const response = await apiFetch('/expenses/expenses/', {
      method: 'POST',
      body: JSON.stringify(newExpense.value),
    })
    if (response.ok) {
      expenses.value.unshift(await response.json())
    } else {
      throw new Error('Failed to add expense.')
    }

    // Reset form
    newExpense.value = {
      expense_date: todayStr,
      description: '',
      amount: 0,
      amortization_start_date: todayStr,
      amortization_end_date: todayStr,
      category: null,
      trip: null,
      is_expense: true,
      currency: null,
    }
    assignDefaultCurrencyAndTrip()
  } catch (error: any) {
    console.error('Error adding expense:', error)
    formError.value = error.response?.data?.detail || 'An error occurred while adding the expense'
  } finally {
    isSubmitting.value = false
  }
}

// Delete expense
const deleteExpense = async (expenseId: number) => {
  if (!expenseId) return
  try {
    const response = await apiFetch(`/expenses/expenses/${expenseId}/`, {
      method: 'DELETE',
    })
    if (response.ok) {
      expenses.value = expenses.value.filter((e) => e.id !== expenseId)
    } else {
      throw new Error('Failed to delete expense.')
    }
  } catch (error) {
    console.error('Error deleting expense:', error)
    tableErrors.value.push("Errore durante l'eliminazione della spesa.")
  }
}

function confirmDelete(expense: Expense) {
  if (confirm('Sei sicuro di voler eliminare questa spesa?')) {
    deleteExpense(expense.id!)
  }
}

// Get category name by ID
const getCategoryName = (categoryId: number | null) => {
  if (!categoryId) return ''
  const category = categories.value.find((c) => c.id === categoryId)
  return category ? category.name : 'Unknown'
}

// Get trip name by ID
const getTripName = (tripId: number | null) => {
  if (!tripId) return ''
  const trip = trips.value.find((t) => t.id === tripId)
  return trip ? trip.name : 'Unknown'
}

async function fetchMetadata() {
  await Promise.all([
    fetchCategories(),
    fetchTrips(),
    fetchExpenses(),
    fetchCurrencies(),
    fetchUserSettings(),
  ])
}

function getCurrencyName(currencyId: number | null) {
  if (!currencyId) return ''
  const currency = currencies.value.find((c) => c.id === currencyId)
  return currency?.code ?? ''
}

function assignDefaultCurrencyAndTrip() {
  if (userSettings.value?.preferred_currency) {
    newExpense.value.currency = userSettings.value.preferred_currency
  }
  if (userSettings.value?.active_trip) {
    newExpense.value.trip = userSettings.value.active_trip
  }
}

// Load data on component mount
onMounted(async () => {
  initialPageLoading.value = true
  try {
    await fetchMetadata()
    assignDefaultCurrencyAndTrip()
  } finally {
    initialPageLoading.value = false
  }
})
</script>

<template>
  <div class="expenses-container" v-if="!initialPageLoading">
    <h1>Expenses List</h1>

    <!-- Add Expense Form -->
    <div class="expense-form">
      <h2>Add New Expense</h2>
      <form @submit.prevent="addExpense">
        <div class="form-row">
          <div class="form-group">
            <label for="expense_date">Expense Date</label>
            <input type="date" id="expense_date" v-model="newExpense.expense_date" required />
          </div>

          <div class="form-group">
            <label for="description">Description</label>
            <input type="text" id="description" v-model="newExpense.description" required />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="amount">Amount</label>
            <input type="number" id="amount" v-model="newExpense.amount" step="0.01" required />
          </div>

          <div class="form-group">
            <label for="currency">Currency</label>
            <select id="currency" v-model="newExpense.currency" required>
              <option value="0" disabled>Select a currency</option>
              <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
                {{ currency.display_name }}
              </option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="amortization_start_date">Amortization Start Date</label>
            <input
              type="date"
              id="amortization_start_date"
              v-model="newExpense.amortization_start_date"
              required
            />
          </div>

          <div class="form-group">
            <label for="amortization_end_date">Amortization End Date</label>
            <input
              type="date"
              id="amortization_end_date"
              v-model="newExpense.amortization_end_date"
              required
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="category">Category</label>
            <select id="category" v-model="newExpense.category" required>
              <option value="0" disabled>Select a category</option>
              <option v-for="category in categories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="trip">Trip</label>
            <select id="trip" v-model="newExpense.trip">
              <option :value="null">None</option>
              <option v-for="trip in trips" :key="trip.id" :value="trip.id">
                {{ trip.name }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="formError" class="error-message">
          {{ formError }}
        </div>

        <button type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Adding...' : 'Add Expense' }}
        </button>
      </form>
    </div>
    <div class="expense-import-csv">
      <p>or <router-link to="/import-expenses-from-csv">import from csv</router-link></p>
    </div>

    <!-- Expenses Table -->
    <div class="expenses-table">
      <div style="display: flex; align-items: center; justify-content: space-between">
        <h2>Expenses</h2>
        <button @click="fetchMetadata" style="margin-left: auto">Reload</button>
      </div>
      <div v-for="msg of tableErrors" :key="msg" class="error-message">{{ msg }}</div>
      <table>
        <thead>
          <tr>
            <th>Creation Date</th>
            <th>Description</th>
            <th>Amount</th>
            <th>Currency</th>
            <th>Amortization Start</th>
            <th>Amortization End</th>
            <th>Category</th>
            <th>Trip</th>
            <th>Is Expense</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="expenses.length === 0">
            <td colspan="9" class="no-data">No expenses found</td>
          </tr>
          <tr v-for="expense in expenses" :key="expense.id">
            <td>{{ expense.expense_date }}</td>
            <td>{{ expense.description }}</td>
            <td>{{ expense.amount }}</td>
            <td>{{ getCurrencyName(expense.currency) }}</td>
            <td>{{ expense.amortization_start_date }}</td>
            <td>{{ expense.amortization_end_date }}</td>
            <td>{{ getCategoryName(expense.category) }}</td>
            <td>{{ getTripName(expense.trip) }}</td>
            <td>{{ expense.is_expense ? 'Yes' : 'No' }}</td>
            <td>
              <button
                @click="confirmDelete(expense)"
                title="Elimina"
                style="background: none; border: none; cursor: pointer"
              >
                <DeleteIcon />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <div class="expenses-container" v-else>
    <p>Loading...</p>
  </div>
</template>

<style scoped>
.expenses-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.expense-import-csv {
  text-align: center;
}
</style>
