<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import apiFetch from '@/utils/apiFetch'
import DeleteIcon from '../../icons/DeleteIcon.vue'
import type { RecurringExpense } from '@/interfaces/RecurringExpense'
import type { ExpenseCategory } from '@/interfaces/ExpenseCategory'
import type { Currency } from '@/interfaces/Currency'
import type { Trip } from '@/interfaces/Trip'
import type { UserSettings } from '@/interfaces/UserSettings'

const todayStr = new Date().toISOString().substring(0, 10)

const initialPageLoading = ref(true)
const recurringExpenses = ref<RecurringExpense[]>([])
const categories = ref<ExpenseCategory[]>([])
const trips = ref<Trip[]>([])
const currencies = ref<Currency[]>([])
const userSettings = ref<UserSettings | null>(null)
const tableErrors = ref<string[]>([])
const formError = ref('')
const isSubmitting = ref(false)
const editingId = ref<number | null>(null)

const newRecurringExpense = ref<RecurringExpense>({
  start_date: todayStr,
  end_date: null,
  amount: 0,
  category: null,
  trip: null,
  schedule: '',
  description: '',
  is_expense: true,
  currency: null,
})

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
    fetchRecurringExpenses(),
    fetchCurrencies(),
    fetchUserSettings(),
  ])
}

async function fetchRecurringExpenses() {
  try {
    const response = await apiFetch('/expenses/recurring-expenses/')
    if (response.ok) {
      recurringExpenses.value = await response.json()
    } else {
      throw new Error('Failed to load recurring expenses.')
    }
  } catch (error) {
    console.error('Error fetching recurring expenses:', error)
    tableErrors.value.push('Failed to load recurring expenses.')
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
      assignDefaultCurrencyAndTrip()
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
    tableErrors.value.push('Failed to load trips.')
  }
}

function assignDefaultCurrencyAndTrip() {
  if (userSettings.value?.preferred_currency) {
    newRecurringExpense.value.currency = userSettings.value.preferred_currency
  }
  if (userSettings.value?.active_trip) {
    newRecurringExpense.value.trip = userSettings.value.active_trip
  }
}

watch(
  () => initialPageLoading.value,
  (newVal) => {
    if (!newVal) {
      assignDefaultCurrencyAndTrip()
    }
  },
)

// Filter categories based on is_expense
const filteredCategories = computed(() => {
  return categories.value.filter((c) => c.for_expense === newRecurringExpense.value.is_expense)
})

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

function getCurrencyName(currencyId: number | null) {
  if (!currencyId) return ''
  const currency = currencies.value.find((c) => c.id === currencyId)
  return currency?.code ?? ''
}

// Update is_expense when category changes
watch(
  () => newRecurringExpense.value.category,
  (categoryId) => {
    if (categoryId) {
      const category = categories.value.find((c) => c.id === categoryId)
      if (category) {
        newRecurringExpense.value.is_expense = category.for_expense
      }
    }
  },
)

// Submit form (create or update)
const submitForm = async () => {
  isSubmitting.value = true
  formError.value = ''

  try {
    // Validate form
    if (!newRecurringExpense.value.start_date) {
      formError.value = 'Start date is required'
      return
    }
    if (!newRecurringExpense.value.description) {
      formError.value = 'Description is required'
      return
    }
    if (!newRecurringExpense.value.schedule) {
      formError.value = 'Schedule is required'
      return
    }
    if (!newRecurringExpense.value.category) {
      formError.value = 'Category is required'
      return
    }
    if (!newRecurringExpense.value.currency) {
      formError.value = 'Currency is required'
      return
    }
    if (
      newRecurringExpense.value.end_date &&
      newRecurringExpense.value.start_date > newRecurringExpense.value.end_date
    ) {
      formError.value = 'Start date must be before or equal to end date'
      return
    }

    const selectedCategory = categories.value.find(
      (c) => c.id === newRecurringExpense.value.category,
    )
    if (!selectedCategory) {
      formError.value = 'Invalid category selected'
      return
    }
    newRecurringExpense.value.is_expense = selectedCategory.for_expense

    let response: Response
    if (editingId.value) {
      // Update existing
      response = await apiFetch(`/expenses/recurring-expenses/${editingId.value}/`, {
        method: 'PATCH',
        body: JSON.stringify(newRecurringExpense.value),
      })
    } else {
      // Create new
      response = await apiFetch('/expenses/recurring-expenses/', {
        method: 'POST',
        body: JSON.stringify(newRecurringExpense.value),
      })
    }

    if (response.ok) {
      const updatedExpense = await response.json()
      if (editingId.value) {
        // Update in list
        const index = recurringExpenses.value.findIndex((e) => e.id === editingId.value)
        if (index !== -1) {
          recurringExpenses.value[index] = updatedExpense
        }
        editingId.value = null
      } else {
        // Add to list
        recurringExpenses.value.unshift(updatedExpense)
      }
      resetForm()
    } else {
      const errorData = await response.json()
      throw new Error(errorData?.detail || 'Failed to save recurring expense.')
    }
  } catch (error: any) {
    console.error('Error saving recurring expense:', error)
    formError.value = error.message || 'An error occurred while saving the recurring expense'
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  newRecurringExpense.value = {
    start_date: todayStr,
    end_date: null,
    amount: 0,
    category: null,
    trip: null,
    schedule: '',
    description: '',
    is_expense: true,
    currency: null,
  }
  editingId.value = null
  assignDefaultCurrencyAndTrip()
}

function editRecurringExpense(expense: RecurringExpense) {
  editingId.value = expense.id!
  newRecurringExpense.value = {
    id: expense.id,
    start_date: expense.start_date,
    end_date: expense.end_date,
    amount: expense.amount,
    category: expense.category,
    trip: expense.trip,
    schedule: expense.schedule,
    description: expense.description,
    is_expense: expense.is_expense,
    currency: expense.currency,
  }
  // Scroll to form
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  resetForm()
}

async function deleteRecurringExpense(expenseId: number) {
  if (!expenseId) return
  if (!confirm('Are you sure you want to delete this recurring expense?')) {
    return
  }
  try {
    const response = await apiFetch(`/expenses/recurring-expenses/${expenseId}/`, {
      method: 'DELETE',
    })
    if (response.ok) {
      recurringExpenses.value = recurringExpenses.value.filter((e) => e.id !== expenseId)
    } else {
      throw new Error('Failed to delete recurring expense.')
    }
  } catch (error) {
    console.error('Error deleting recurring expense:', error)
    tableErrors.value.push('Failed to delete recurring expense.')
  }
}
</script>

<template>
  <div v-if="!initialPageLoading">
    <h1 class="text-2xl font-bold mb-8">Recurring Expenses</h1>

    <!-- Create/Edit Form -->
    <h2 class="text-xl font-bold mb-3">
      {{ editingId ? 'Edit Recurring Expense' : 'Add Recurring Expense' }}
    </h2>
    <form
      class="form grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      @submit.prevent="submitForm"
    >
      <div>
        <label for="description">Description</label>
        <input
          type="text"
          id="description"
          class="input input-border w-full"
          v-model="newRecurringExpense.description"
          required
        />
      </div>

      <div>
        <label for="amount">Amount</label>
        <input
          type="number"
          id="amount"
          class="input input-border w-full"
          v-model="newRecurringExpense.amount"
          step="0.01"
          required
        />
      </div>

      <div>
        <label for="currency">Currency</label>
        <select
          class="select input input-border w-full"
          id="currency"
          v-model="newRecurringExpense.currency"
          required
        >
          <option :value="null" disabled>Select a currency</option>
          <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
            {{ currency.display_name }}
          </option>
        </select>
      </div>

      <div>
        <label for="start_date">Start Date</label>
        <input
          type="date"
          id="start_date"
          class="input input-border w-full"
          v-model="newRecurringExpense.start_date"
          required
        />
      </div>

      <div>
        <label for="end_date">End Date (optional)</label>
        <input
          type="date"
          id="end_date"
          class="input input-border w-full"
          v-model="newRecurringExpense.end_date"
        />
      </div>

      <div>
        <label for="schedule">Schedule (Crontab)</label>
        <input
          type="text"
          id="schedule"
          class="input input-border w-full"
          v-model="newRecurringExpense.schedule"
          placeholder="0 0 * * *"
          required
        />
        <small class="text-gray-500"
          >Format: minute hour day month weekday (e.g., "0 0 * * *" for daily)</small
        >
      </div>

      <div>
        <label for="category">Category</label>
        <select
          class="select input input-border w-full"
          id="category"
          v-model="newRecurringExpense.category"
          required
        >
          <option :value="null" disabled>Select a category</option>
          <option v-for="category in filteredCategories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
      </div>

      <div>
        <label for="trip">Trip (optional)</label>
        <select
          class="select input input-border w-full"
          id="trip"
          v-model="newRecurringExpense.trip"
        >
          <option :value="null">Select a trip</option>
          <option v-for="trip in trips" :key="trip.id" :value="trip.id">
            {{ trip.name }}
          </option>
        </select>
      </div>

      <div>
        <label for="is_expense" class="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_expense"
            class="checkbox"
            v-model="newRecurringExpense.is_expense"
            disabled
          />
          Is Expense (derived from category)
        </label>
      </div>

      <div class="col-span-full flex gap-2">
        <button type="submit" :disabled="isSubmitting" class="btn btn-primary">
          {{ isSubmitting ? 'Saving...' : editingId ? 'Update' : 'Add' }}
        </button>
        <button v-if="editingId" type="button" @click="cancelEdit" class="btn btn-secondary">
          Cancel
        </button>
      </div>
    </form>
    <div v-if="formError" class="text-red-500 my-4">{{ formError }}</div>

    <!-- List/Table -->
    <h2 class="text-xl font-bold mb-3 my-8">Recurring Expenses List</h2>
    <div v-for="msg of tableErrors" :key="msg" class="text-red-500 my-4">{{ msg }}</div>
    <div class="overflow-x-auto">
      <table class="table">
        <thead>
          <tr>
            <th>Description</th>
            <th>Amount</th>
            <th>Currency</th>
            <th>Schedule</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Category</th>
            <th>Trip</th>
            <th>Type</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="recurringExpenses.length === 0">
            <td colspan="10" class="no-data">No recurring expenses found</td>
          </tr>
          <tr v-for="expense in recurringExpenses" :key="expense.id">
            <td>{{ expense.description }}</td>
            <td>{{ expense.amount }}</td>
            <td>{{ getCurrencyName(expense.currency) }}</td>
            <td>{{ expense.schedule }}</td>
            <td>{{ expense.start_date }}</td>
            <td>{{ expense.end_date || '-' }}</td>
            <td>{{ getCategoryName(expense.category) }}</td>
            <td>{{ getTripName(expense.trip) || '-' }}</td>
            <td>{{ expense.is_expense ? 'Expense' : 'Income' }}</td>
            <td>
              <div class="flex gap-2">
                <button
                  @click="editRecurringExpense(expense)"
                  class="btn btn-sm btn-primary"
                  title="Edit"
                >
                  Edit
                </button>
                <button
                  @click="deleteRecurringExpense(expense.id!)"
                  title="Delete"
                  style="background: none; border: none; cursor: pointer"
                >
                  <DeleteIcon />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <div v-else-if="tableErrors.length > 0">
    <p>{{ tableErrors.join('\n') }}</p>
  </div>
  <div v-else>
    <p>Loading...</p>
  </div>
</template>

<style scoped></style>
