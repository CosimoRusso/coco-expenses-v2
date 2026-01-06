<script setup lang="ts">
import { computed, ref } from 'vue'
import DeleteIcon from '../../icons/DeleteIcon.vue'
import EditIcon from '../../icons/EditIcon.vue'
import apiFetch from '@/utils/apiFetch'

import type { Expense } from '@/interfaces/Expense'
import type { ExpenseCategory } from '@/interfaces/ExpenseCategory'
import type { Currency } from '@/interfaces/Currency'
import type { Trip } from '@/interfaces/Trip'
import type { UserSettings } from '@/interfaces/UserSettings'

const props = defineProps<{
  initialPageLoading: boolean
  categories: ExpenseCategory[]
  trips: Trip[]
  currencies: Currency[]
  userSettings: UserSettings | null
  expenses: Expense[]
  currentPage: number
  totalCount: number
  hasNextPage: boolean
  hasPreviousPage: boolean
}>()

const emit = defineEmits<{
  (e: 'expense-deleted', expenseId: number): void
  (e: 'reload-expenses'): void
  (e: 'page-changed', page: number): void
  (e: 'edit-expense', expense: Expense): void
}>()

const tableErrors = ref<string[]>([])

// Filter state
const filterCategory = defineModel<number | null>('filterCategory', { required: false })
const filterTrip = defineModel<number | null>('filterTrip', { required: false })
const filterIsExpense = defineModel<boolean | null>('filterIsExpense', { required: false })
const filterStartDate = defineModel<string | null>('filterStartDate', { required: false })
const filterEndDate = defineModel<string | null>('filterEndDate', { required: false })

// Delete expense
const deleteExpense = async (expenseId: number) => {
  if (!expenseId) return
  try {
    const response = await apiFetch(`/expenses/expenses/${expenseId}/`, {
      method: 'DELETE',
    })
    if (response.ok) {
      emit('expense-deleted', expenseId)
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

function editExpense(expense: Expense) {
  emit('edit-expense', expense)
}

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

function goToNextPage() {
  if (props.hasNextPage) {
    emit('page-changed', props.currentPage + 1)
  }
}

function goToPreviousPage() {
  if (props.hasPreviousPage) {
    emit('page-changed', props.currentPage - 1)
  }
}

const pageSize = 50

const totalPages = computed(() => Math.ceil(props.totalCount / pageSize))
</script>

<template>
  <div class="expenses-table">
    <!-- Filter Bar -->
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <div>
        <label for="filter-category">Category</label>
        <select
          class="select input input-border w-full"
          id="filter-category"
          v-model="filterCategory"
        >
          <option :value="null">All Categories</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
      </div>

      <div>
        <label for="filter-trip">Trip</label>
        <select class="select input input-border w-full" id="filter-trip" v-model="filterTrip">
          <option :value="null">All Trips</option>
          <option v-for="trip in trips" :key="trip.id" :value="trip.id">
            {{ trip.name }}
          </option>
        </select>
      </div>

      <div>
        <label for="filter-is-expense">Type</label>
        <select
          class="select input input-border w-full"
          id="filter-is-expense"
          v-model="filterIsExpense"
        >
          <option :value="null">All</option>
          <option :value="true">Expenses</option>
          <option :value="false">Income</option>
        </select>
      </div>

      <div>
        <label for="filter-start-date">Start Date</label>
        <input
          type="date"
          id="filter-start-date"
          class="input input-bordered w-full"
          v-model="filterStartDate"
        />
      </div>

      <div>
        <label for="filter-end-date">End Date</label>
        <input
          type="date"
          id="filter-end-date"
          class="input input-bordered w-full"
          v-model="filterEndDate"
        />
      </div>
    </div>

    <div class="flex items-center justify-between my-8">
      <h2 class="text-2xl font-bold">Expenses</h2>
      <button class="btn btn-primary" @click="emit('reload-expenses')">Reload</button>
    </div>
    <div v-for="msg of tableErrors" :key="msg" class="error-message">{{ msg }}</div>
    <div class="overflow-x-auto">
      <table class="table">
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
          <tr v-if="props.expenses.length === 0">
            <td colspan="9" class="no-data">No expenses found</td>
          </tr>
          <tr v-for="expense in props.expenses" :key="expense.id">
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
              <div class="flex gap-2">
                <button
                  @click="editExpense(expense)"
                  title="Modifica"
                  style="background: none; border: none; cursor: pointer"
                >
                  <EditIcon />
                </button>
                <button
                  @click="confirmDelete(expense)"
                  title="Elimina"
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
    <!-- Pagination Controls -->
    <div v-if="totalCount > 0" class="flex items-center justify-between mt-4">
      <div class="text-sm text-gray-600">
        Showing {{ (currentPage - 1) * pageSize + 1 }} to
        {{ Math.min(currentPage * pageSize, totalCount) }} of {{ totalCount }} expenses
      </div>
      <div class="flex items-center gap-2">
        <button class="btn btn-sm" :disabled="!hasPreviousPage" @click="goToPreviousPage">
          Previous
        </button>
        <span class="text-sm"> Page {{ currentPage }} of {{ totalPages }} </span>
        <button class="btn btn-sm" :disabled="!hasNextPage" @click="goToNextPage">Next</button>
      </div>
    </div>
  </div>
</template>
