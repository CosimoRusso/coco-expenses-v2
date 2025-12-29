<script setup lang="ts">
import { ref } from 'vue'
import DeleteIcon from '../../icons/DeleteIcon.vue'
import apiFetch from '@/utils/apiFetch'

import type { Expense } from '@/interfaces/Expense'
import type { ExpenseCategory } from '@/interfaces/ExpenseCategory'
import type { Currency } from '@/interfaces/Currency'
import type { Trip } from '@/interfaces/Trip'
import type { UserSettings } from '@/interfaces/UserSettings'

const props = defineProps<{
      initialPageLoading: boolean,
      categories: ExpenseCategory[],
      trips: Trip[],
      currencies: Currency[],
      userSettings: UserSettings | null,
      expenses: Expense[],
    }>();

const emit = defineEmits<{
  (e: 'expense-deleted', expenseId: number): void
  (e: 'reload-expenses'): void
}>();

const tableErrors = ref<string[]>([])

// Filter state
const filterCategory = defineModel<number | null>('filterCategory', { required: false })
const filterTrip = defineModel<number | null>('filterTrip', { required: false })
const filterIsExpense = defineModel<boolean | null>('filterIsExpense', { required: false })


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


</script>

<template>
    <div class="expenses-table">
      <!-- Filter Bar -->
    <div class="filters-bar">
      <div class="filter-group">
        <label for="filter-category">Category</label>
        <select id="filter-category" v-model="filterCategory" @change="emit('reload-expenses')">
          <option :value="null">All Categories</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label for="filter-trip">Trip</label>
        <select id="filter-trip" v-model="filterTrip" @change="emit('reload-expenses')">
          <option :value="null">All Trips</option>
          <option v-for="trip in trips" :key="trip.id" :value="trip.id">
            {{ trip.name }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label for="filter-is-expense">Type</label>
        <select id="filter-is-expense" v-model="filterIsExpense" @change="emit('reload-expenses')">
          <option :value="null">All</option>
          <option :value="true">Expenses</option>
          <option :value="false">Income</option>
        </select>
      </div>
    </div>


      <div style="display: flex; align-items: center; justify-content: space-between">
        <h2>Expenses</h2>
        <button @click="emit('reload-expenses')" style="margin-left: auto">Reload</button>
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
</template>