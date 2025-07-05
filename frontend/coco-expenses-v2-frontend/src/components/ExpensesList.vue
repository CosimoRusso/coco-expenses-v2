<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface Expense {
  id?: number
  expense_date: string
  description: string
  forecast_amount: number
  actual_amount: number
  amortization_start_date: string
  amortization_end_date: string
  category: number | null
  trip: number | null
  is_expense: boolean
}

interface Category {
  id: number
  name: string
}

interface Trip {
  id: number
  name: string
}

// Data
const expenses = ref<Expense[]>([])
const categories = ref<Category[]>([])
const trips = ref<Trip[]>([])

// New expense form
const newExpense = ref<Expense>({
  expense_date: '',
  description: '',
  forecast_amount: 0,
  actual_amount: 0,
  amortization_start_date: '',
  amortization_end_date: '',
  category: null,
  trip: null,
  is_expense: true,
})

// Form error handling
const formError = ref('')
const tableErrors = ref<string[]>([])
const isSubmitting = ref(false)

// Fetch expenses
const fetchExpenses = async () => {
  try {
    const response = await axios.get('/api/expenses/expenses/')
    expenses.value = response.data
  } catch (error) {
    console.error('Error fetching expenses:', error)
    tableErrors.value.push('Failed to load categories.')
  }
}

async function fetchCategories() {
  try {
    const response = await axios.get('/api/expenses/expense-categories/')
    categories.value = response.data
  } catch (error) {
    console.error('Error fetching categories:', error)
    tableErrors.value.push('Failed to load categories.')
  }
}
async function fetchTrips() {
  try {
    const response = await axios.get('/api/expenses/trips/')
    trips.value = response.data
  } catch (error) {
    console.error('Error fetching trips:', error)
    tableErrors.value.push('Failed to load trips.')
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

    // Submit form
    const response = await axios.post('/api/expenses/', newExpense.value)

    // Add new expense to list
    expenses.value.push(response.data)

    // Reset form
    newExpense.value = {
      expense_date: '',
      description: '',
      forecast_amount: 0,
      actual_amount: 0,
      amortization_start_date: '',
      amortization_end_date: '',
      category: null,
      trip: null,
      is_expense: true,
    }
  } catch (error: any) {
    console.error('Error adding expense:', error)
    formError.value = error.response?.data?.detail || 'An error occurred while adding the expense'
  } finally {
    isSubmitting.value = false
  }
}

// Format date for display
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

// Get category name by ID
const getCategoryName = (categoryId: number) => {
  const category = categories.value.find((c) => c.id === categoryId)
  return category ? category.name : 'Unknown'
}

// Get trip name by ID
const getTripName = (tripId: number | null) => {
  if (!tripId) return ''
  const trip = trips.value.find((t) => t.id === tripId)
  return trip ? trip.name : 'Unknown'
}

async function fetchCategoriesTripsAndExpenses() {
  await fetchCategories()
  await fetchTrips()
  await fetchExpenses()
}

// Load data on component mount
onMounted(() => {
  fetchCategoriesTripsAndExpenses().then(() => {})
})
</script>

<template>
  <div class="expenses-container">
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
            <label for="forecast_amount">Forecast Amount</label>
            <input
              type="number"
              id="forecast_amount"
              v-model="newExpense.forecast_amount"
              step="0.01"
              required
            />
          </div>

          <div class="form-group">
            <label for="actual_amount">Actual Amount</label>
            <input
              type="number"
              id="actual_amount"
              v-model="newExpense.actual_amount"
              step="0.01"
              required
            />
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
      <p>or <a href="/import-expenses-from-csv">import from csv</a></p>
    </div>

    <!-- Expenses Table -->
    <div class="expenses-table">
      <div style="display: flex; align-items: center; justify-content: space-between">
        <h2>Expenses</h2>
        <button @click="fetchCategoriesTripsAndExpenses" style="margin-left: auto">Reload</button>
      </div>
      <div v-for="msg of tableErrors" :key="msg" class="error-message">{{ msg }}</div>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Forecast Amount</th>
            <th>Actual Amount</th>
            <th>Amortization Start</th>
            <th>Amortization End</th>
            <th>Category</th>
            <th>Trip</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="expenses.length === 0">
            <td colspan="8" class="no-data">No expenses found</td>
          </tr>
          <tr v-for="expense in expenses" :key="expense.id">
            <td>{{ formatDate(expense.expense_date) }}</td>
            <td>{{ expense.description }}</td>
            <td>{{ expense.forecast_amount }}</td>
            <td>{{ expense.actual_amount }}</td>
            <td>{{ formatDate(expense.amortization_start_date) }}</td>
            <td>{{ formatDate(expense.amortization_end_date) }}</td>
            <td>{{ getCategoryName(expense.category) }}</td>
            <td>{{ getTripName(expense.trip) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.expenses-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  color: #333;
  margin-bottom: 20px;
  text-align: center;
}

h2 {
  color: #555;
  margin-bottom: 15px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
}

/* Form Styles */
.expense-form {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
}

label {
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}

input,
select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

button {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 10px;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #45a049;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.error-message {
  color: #d32f2f;
  margin-top: 10px;
  font-size: 14px;
}

/* Table Styles */
.expenses-table {
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

th {
  background-color: #f2f2f2;
  font-weight: bold;
  color: #333;
}

tr:hover {
  background-color: #f5f5f5;
}

.no-data {
  text-align: center;
  color: #888;
  padding: 20px;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 10px;
  }

  table {
    display: block;
    overflow-x: auto;
  }
}
.expense-import-csv {
  text-align: center;
}
</style>
