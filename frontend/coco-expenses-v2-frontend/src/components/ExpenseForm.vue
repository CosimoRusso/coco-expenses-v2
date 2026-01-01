<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import apiFetch from '@/utils/apiFetch'
import type { Expense } from '@/interfaces/Expense'
import type { ExpenseCategory } from '@/interfaces/ExpenseCategory'
import type { Currency } from '@/interfaces/Currency'
import type { Trip } from '@/interfaces/Trip'
import type { UserSettings } from '@/interfaces/UserSettings'

// Constants
const todayStr = new Date().toISOString().substring(0, 10)

const props = defineProps<{
  initialPageLoading: boolean
  categories: ExpenseCategory[]
  trips: Trip[]
  currencies: Currency[]
  userSettings: UserSettings | null
}>()

const emit = defineEmits<{
  (e: 'expense-added', expense: Expense): void
}>()

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

const expenseDatePicker = ref<HTMLInputElement | null>(null)
const amortizationStartDatePicker = ref<HTMLInputElement | null>(null)
const amortizationEndDatePicker = ref<HTMLInputElement | null>(null)

// Get category name by ID
const getCategoryName = (categoryId: number | null) => {
  if (!categoryId) return ''
  const category = props.categories.find((c) => c.id === categoryId)
  return category ? category.name : 'Unknown'
}

// Get trip name by ID
const getTripName = (tripId: number | null) => {
  if (!tripId) return ''
  const trip = props.trips.find((t) => t.id === tripId)
  return trip ? trip.name : 'Unknown'
}

function getCurrencyName(currencyId: number | null) {
  if (!currencyId) return ''
  const currency = props.currencies.find((c) => c.id === currencyId)
  return currency?.code ?? ''
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

    const _selectedCategory = props.categories.find((c) => c.id === newExpense.value.category)
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
      const newExpense = await response.json()
      emit('expense-added', newExpense)
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

function assignDefaultCurrencyAndTrip() {
  if (props.userSettings?.preferred_currency) {
    newExpense.value.currency = props.userSettings.preferred_currency
  }
  if (props.userSettings?.active_trip) {
    newExpense.value.trip = props.userSettings.active_trip
  }
}

watch(
  () => props.initialPageLoading,
  (newVal) => {
    if (newVal) {
      assignDefaultCurrencyAndTrip()
    }
  },
)
</script>

<template>
  <h2 class="text-xl font-bold mb-3">Add New Expense</h2>
  <form
    class="form grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    @submit.prevent="addExpense"
  >
    <div>
      <label for="expense_date">Expense Date</label>

      <input
        class="input input-border"
        type="date"
        id="expense_date"
        v-model="newExpense.expense_date"
      />
    </div>

    <div>
      <label for="description">Description</label>
      <input type="text" id="description" class="input" v-model="newExpense.description" required />
    </div>

    <div>
      <label for="amount">Amount</label>
      <input
        type="number"
        id="amount"
        v-model="newExpense.amount"
        step="0.01"
        required
        class="input"
      />
    </div>

    <div>
      <label for="currency">Currency</label>
      <select class="select" id="currency" v-model="newExpense.currency" required>
        <option value="0" disabled>Select a currency</option>
        <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
          {{ currency.display_name }}
        </option>
      </select>
    </div>

    <div>
      <label for="amortization_start_date">Amortization Start Date</label>
      <input
        type="date"
        class="input input-border"
        id="amortization_start_date"
        v-model="newExpense.amortization_start_date"
        required
      />
    </div>

    <div>
      <label for="amortization_end_date">Amortization End Date</label>
      <input
        type="date"
        class="input input-border"
        id="amortization_end_date"
        v-model="newExpense.amortization_end_date"
        required
      />
    </div>

    <div>
      <label for="category">Category</label>
      <select
        class="select input input-border"
        id="category"
        v-model="newExpense.category"
        required
      >
        <option value="0" disabled>Select a category</option>
        <option v-for="category in categories" :key="category.id" :value="category.id">
          {{ category.name }}
        </option>
      </select>
    </div>

    <div>
      <label for="trip">Trip</label>
      <select class="select input input-border w-full" id="trip" v-model="newExpense.trip">
        <option :value="null">Select a trip</option>
        <option v-for="trip in trips" :key="trip.id" :value="trip.id">
          {{ trip.name }}
        </option>
      </select>
    </div>
    <div class="col-span-full"></div>
    <button type="submit" :disabled="isSubmitting" class="btn btn-primary col-span-full">
      {{ isSubmitting ? 'Adding...' : 'Add Expense' }}
    </button>
  </form>
  <div v-if="formError" class="text-red-50 my-4">
    {{ formError }}
  </div>
  <div class="my-4 text-center">
    <p>
      or
      <router-link class="text-primary" to="/import-expenses-from-csv">import from csv</router-link>
    </p>
  </div>
</template>
