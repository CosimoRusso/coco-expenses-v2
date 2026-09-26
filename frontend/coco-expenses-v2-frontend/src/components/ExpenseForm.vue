<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import apiFetch from '@/utils/apiFetch'
import type { Expense } from '@/interfaces/Expense'
import type { ExpenseCategory } from '@/interfaces/ExpenseCategory'
import type { Currency } from '@/interfaces/Currency'
import type { Friend } from '@/interfaces/Friend'
import type { SharedExpenseRequest } from '@/interfaces/Notification'
import type { Trip } from '@/interfaces/Trip'
import type { UserSettings } from '@/interfaces/UserSettings'
import MultiSelect from '@/components/MultiSelect.vue'

// Constants
const todayStr = new Date().toISOString().substring(0, 10)

const props = defineProps<{
  initialPageLoading: boolean
  categories: ExpenseCategory[]
  trips: Trip[]
  currencies: Currency[]
  friends: Friend[]
  userSettings: UserSettings | null
  editingExpense?: Expense | null
  // A friend's shared expense this form completes with the current user's quota
  sharedExpenseRequest?: SharedExpenseRequest | null
}>()

const emit = defineEmits<{
  (e: 'expense-added', expense: Expense): void
  (e: 'expense-updated', expense: Expense): void
  (e: 'shared-expense-request-cancelled'): void
}>()

function emptyExpense(): Expense {
  return {
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
}

// New expense form
const newExpense = ref<Expense>(emptyExpense())

// Form error handling
const formError = ref('')
const isSubmitting = ref(false)

const isEditing = computed(() => !!props.editingExpense?.id)
const isCompletingShare = computed(() => !isEditing.value && !!props.sharedExpenseRequest)

const heading = computed(() => {
  if (isEditing.value) return 'Edit Expense'
  if (isCompletingShare.value) return 'Complete Shared Expense'
  return 'Add New Expense'
})

// Filter active categories and trips
const activeCategories = computed(() => props.categories.filter((cat) => cat.is_active))
const activeTrips = computed(() => props.trips.filter((trip) => trip.is_active))
const friendOptions = computed(() =>
  props.friends.map((friend) => ({
    value: friend.id,
    label: `${friend.first_name} ${friend.last_name}`,
  })),
)

// Friends to share the expense with
const selectedFriendIds = ref<number[]>([])

function requestBody() {
  if (isCompletingShare.value) {
    return { ...newExpense.value, shared_expense_participant: props.sharedExpenseRequest!.id }
  }
  if (isEditing.value) {
    return newExpense.value
  }
  return { ...newExpense.value, shared_with: selectedFriendIds.value }
}

// Add or update expense
const addOrUpdateExpense = async () => {
  isSubmitting.value = true
  formError.value = ''

  try {
    // Validate form
    if (!newExpense.value.expense_date) {
      formError.value = 'Expense date is required'
      isSubmitting.value = false
      return
    }
    if (!newExpense.value.description) {
      formError.value = 'Description is required'
      isSubmitting.value = false
      return
    }
    if (!newExpense.value.category) {
      formError.value = 'Category is required'
      isSubmitting.value = false
      return
    }
    if (!newExpense.value.amortization_start_date || !newExpense.value.amortization_end_date) {
      formError.value = 'Amortization dates are required'
      isSubmitting.value = false
      return
    }

    const _selectedCategory = props.categories.find((c) => c.id === newExpense.value.category)
    if (!_selectedCategory) {
      formError.value = 'Invalid category selected'
      isSubmitting.value = false
      return
    }
    newExpense.value.is_expense = _selectedCategory.for_expense

    // Submit form
    let response: Response
    if (isEditing.value) {
      // Update existing expense
      response = await apiFetch(`/expenses/expenses/${props.editingExpense!.id}/`, {
        method: 'PUT',
        body: JSON.stringify(requestBody()),
      })
    } else {
      // Create new expense
      response = await apiFetch('/expenses/expenses/', {
        method: 'POST',
        body: JSON.stringify(requestBody()),
      })
    }

    if (response.ok) {
      const updatedExpense = await response.json()
      if (isEditing.value) {
        emit('expense-updated', updatedExpense)
        // Form will be reset by watch when editingExpense becomes null
      } else {
        emit('expense-added', updatedExpense)
        resetForm()
      }
    } else {
      throw new Error(isEditing.value ? 'Failed to update expense.' : 'Failed to add expense.')
    }
  } catch (error: any) {
    console.error('Error saving expense:', error)
    formError.value = error.response?.data?.detail || 'An error occurred while saving the expense'
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  newExpense.value = emptyExpense()
  selectedFriendIds.value = []
  assignDefaultCurrencyAndTrip()
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

// Watch for editing expense changes and populate form
watch(
  () => props.editingExpense,
  (expense) => {
    if (expense && expense.id) {
      newExpense.value = {
        expense_date: expense.expense_date,
        description: expense.description,
        amount: expense.amount,
        amortization_start_date: expense.amortization_start_date,
        amortization_end_date: expense.amortization_end_date,
        category: expense.category,
        trip: expense.trip,
        is_expense: expense.is_expense,
        currency: expense.currency,
      }
    } else {
      // Reset form when not editing
      resetForm()
    }
  },
  { immediate: true },
)

// Registered after the editing watch, so its prefill is not overwritten by the reset above
watch(
  () => props.sharedExpenseRequest,
  (request) => {
    if (!request) {
      resetForm()
      return
    }
    newExpense.value.description = request.description
    newExpense.value.amount = Number(request.quota)
    newExpense.value.currency = request.currency
  },
  { immediate: true },
)
</script>

<template>
  <h2 class="text-xl font-bold mb-3">{{ heading }}</h2>
  <p v-if="isCompletingShare" class="mb-3">
    {{ sharedExpenseRequest!.created_by }} shared "{{ sharedExpenseRequest!.description }}" with
    you, for a total of {{ sharedExpenseRequest!.total_amount }}. Your quota is
    {{ sharedExpenseRequest!.quota }}.
  </p>
  <form
    class="form grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    @submit.prevent="addOrUpdateExpense"
  >
    <div>
      <label for="expense_date">Expense Date</label>

      <input
        class="input input-border w-full"
        type="date"
        id="expense_date"
        v-model="newExpense.expense_date"
      />
    </div>

    <div>
      <label for="description">Description</label>
      <input
        type="text"
        id="description"
        class="input input-border w-full"
        v-model="newExpense.description"
        required
      />
    </div>

    <div>
      <label for="amount">Amount</label>
      <input
        type="number"
        id="amount"
        v-model="newExpense.amount"
        step="0.01"
        required
        :disabled="isCompletingShare"
        class="input input-border w-full"
      />
    </div>

    <div>
      <label for="currency">Currency</label>
      <select
        class="select w-full"
        id="currency"
        v-model="newExpense.currency"
        :disabled="isCompletingShare"
        required
      >
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
        class="input input-border w-full"
        id="amortization_start_date"
        v-model="newExpense.amortization_start_date"
        required
      />
    </div>

    <div>
      <label for="amortization_end_date">Amortization End Date</label>
      <input
        type="date"
        class="input input-border w-full"
        id="amortization_end_date"
        v-model="newExpense.amortization_end_date"
        required
      />
    </div>

    <div>
      <label for="category">Category</label>
      <select
        class="select input input-border w-full"
        id="category"
        v-model="newExpense.category"
        required
      >
        <option value="0" disabled>Select a category</option>
        <option v-for="category in activeCategories" :key="category.id" :value="category.id">
          {{ category.name }}
        </option>
      </select>
    </div>

    <div>
      <label for="trip">Trip</label>
      <select class="select input input-border w-full" id="trip" v-model="newExpense.trip">
        <option :value="null">Select a trip</option>
        <option v-for="trip in activeTrips" :key="trip.id" :value="trip.id">
          {{ trip.name }}
        </option>
      </select>
    </div>
    <div v-if="!isEditing && !isCompletingShare">
      <label for="friends">Share with</label>
      <MultiSelect
        id="friends"
        v-model="selectedFriendIds"
        :options="friendOptions"
        placeholder="Select friends"
        emptyText="No friends yet"
      />
    </div>
    <div class="col-span-full"></div>
    <button type="submit" :disabled="isSubmitting" class="btn btn-primary col-span-full">
      {{
        isSubmitting
          ? isEditing
            ? 'Updating...'
            : 'Adding...'
          : isEditing
            ? 'Update Expense'
            : 'Add Expense'
      }}
    </button>
    <button
      v-if="isCompletingShare"
      type="button"
      class="btn col-span-full"
      @click="emit('shared-expense-request-cancelled')"
    >
      Cancel
    </button>
  </form>
  <div v-if="formError" class="text-red-50 my-4">
    {{ formError }}
  </div>
  <div class="my-4 text-center">
    <p>
      or
      <router-link class="text-primary" to="/import-expenses-from-csv">import from csv</router-link>
      <span> / </span>
      <router-link class="text-primary" to="/export-expenses-to-csv">export to csv</router-link>
    </p>
  </div>
</template>
