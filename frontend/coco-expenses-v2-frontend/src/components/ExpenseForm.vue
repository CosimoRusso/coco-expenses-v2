<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import apiFetch from '@/utils/apiFetch'
import type { Expense } from '@/interfaces/Expense'
import type { ExpenseCategory } from '@/interfaces/ExpenseCategory'
import type { Currency } from '@/interfaces/Currency'
import type { Friend } from '@/interfaces/Friend'
import type { SharedExpenseRequest } from '@/interfaces/Notification'
import type { PaymentMethod } from '@/interfaces/PaymentMethod'
import type { Trip } from '@/interfaces/Trip'
import type { UserSettings } from '@/interfaces/UserSettings'
import MultiSelect, { type MultiSelectOption } from '@/components/MultiSelect.vue'
import SplitPanel, { type SplitParticipant } from '@/components/SplitPanel.vue'
import { useUserStore } from '@/stores/user'
import {
  fromCents,
  splitEqually,
  splitError,
  toCents,
  type Quotas,
  type SplitMode,
} from '@/utils/split'

// Constants
const todayStr = new Date().toISOString().substring(0, 10)

const props = defineProps<{
  initialPageLoading: boolean
  categories: ExpenseCategory[]
  trips: Trip[]
  paymentMethods: PaymentMethod[]
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
    payment_method: null,
    is_expense: true,
    currency: null,
  }
}

const userStore = useUserStore()

// New expense form
const newExpense = ref<Expense>(emptyExpense())

// Form error handling
const formError = ref('')
const isSubmitting = ref(false)

const isEditing = computed(() => !!props.editingExpense?.id)
const isCompletingShare = computed(() => !isEditing.value && !!props.sharedExpenseRequest)
const canShare = computed(() => !isCompletingShare.value)
// Other people to share the expense with
const selectedFriendIds = ref<number[]>([])
// The shared expense being edited, whose total, currency and people are shared by everyone
const editingShared = computed(
  () => (isEditing.value && props.editingExpense?.shared_expense) || null,
)
const myParticipant = computed(() =>
  editingShared.value?.participants.find(
    (participant) => participant.id === props.editingExpense?.shared_expense_participant,
  ),
)

const heading = computed(() => {
  if (isEditing.value) return 'Edit Expense'
  if (isCompletingShare.value) return 'Complete Shared Expense'
  return 'Add New Expense'
})

// Filter active categories and trips
const activeCategories = computed(() => props.categories.filter((cat) => cat.is_active))
const activeTrips = computed(() => props.trips.filter((trip) => trip.is_active))
const activePaymentMethods = computed(() =>
  props.paymentMethods.filter((paymentMethod) => paymentMethod.is_active),
)
// Friends, plus the other participants of the shared expense being edited even when they
// are not friends; its creator cannot be removed by anyone else
const friendOptions = computed(() => {
  const people = [
    ...props.friends.map((friend) => ({ ...friend, user_id: friend.id })),
    ...(editingShared.value?.participants ?? []),
  ]
  const creatorId = editingShared.value?.created_by
  const options = new Map<number, MultiSelectOption>()
  for (const person of people) {
    if (person.user_id === myParticipant.value?.user_id || options.has(person.user_id)) continue
    options.set(person.user_id, {
      value: person.user_id,
      label: `${person.first_name} ${person.last_name}`,
      disabled: person.user_id === creatorId,
    })
  }
  return [...options.values()]
})
const isSharing = computed(() => !!editingShared.value || selectedFriendIds.value.length > 0)

const splitMode = ref<SplitMode>('equally')
const customQuotas = ref<Quotas>({})
const myUserId = computed(() => myParticipant.value?.user_id ?? userStore.id)
const creatorId = computed(() => editingShared.value?.created_by ?? myUserId.value)
const splitParticipants = computed<SplitParticipant[]>(() => {
  const labels = new Map(friendOptions.value.map((option) => [option.value, option.label]))
  const others = selectedFriendIds.value.map((userId) => ({
    userId,
    label: labels.get(userId) ?? '',
  }))
  return [{ userId: myUserId.value!, label: 'You' }, ...others]
})
// Everyone sharing the expense, the creator first
const splitUserIds = computed(() => {
  const ids = splitParticipants.value.map((participant) => participant.userId)
  return [creatorId.value!, ...ids.filter((id) => id !== creatorId.value)]
})
const customSplitError = computed(() =>
  isSharing.value && splitMode.value === 'amount'
    ? splitError(Number(newExpense.value.amount), customQuotas.value, splitUserIds.value)
    : '',
)
const currencySymbol = computed(
  () =>
    props.currencies.find((currency) => currency.id === newExpense.value.currency)?.symbol ?? '',
)

// Without a split the backend splits the total equally
function splitBody() {
  if (splitMode.value === 'equally') return {}
  const split = splitUserIds.value.map((user) => ({
    user,
    quota: fromCents(toCents(customQuotas.value[user])),
  }))
  return { split }
}

// A split the editor keeps as it is: equal when it matches the equal split
function loadSplit(participants: { user_id: number; quota: string }[], total: number) {
  const quotas = Object.fromEntries(participants.map((p) => [p.user_id, p.quota]))
  const userIds = participants.map((participant) => participant.user_id)
  const creator = editingShared.value!.created_by
  const equal = splitEqually(total, [creator, ...userIds.filter((id) => id !== creator)])
  const isEqual = userIds.every((userId) => equal[userId] === quotas[userId])
  splitMode.value = isEqual ? 'equally' : 'amount'
  customQuotas.value = quotas
}

function requestBody() {
  if (isCompletingShare.value) {
    return { ...newExpense.value, shared_expense_participant: props.sharedExpenseRequest!.id }
  }
  const split = isSharing.value ? splitBody() : {}
  return { ...newExpense.value, shared_with: selectedFriendIds.value, ...split }
}

// The first validation message of a rejected request, or `fallback`
async function errorMessage(response: Response, fallback: string): Promise<string> {
  const data = await response.json().catch(() => null)
  const [first] = data ? Object.values(data).flat() : []
  return typeof first === 'string' ? first : fallback
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
    if (customSplitError.value) {
      formError.value = customSplitError.value
      isSubmitting.value = false
      return
    }

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
      formError.value = await errorMessage(
        response,
        isEditing.value ? 'Failed to update expense.' : 'Failed to add expense.',
      )
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
  splitMode.value = 'equally'
  customQuotas.value = {}
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
      selectedFriendIds.value = []
      splitMode.value = 'equally'
      customQuotas.value = {}
      newExpense.value = {
        expense_date: expense.expense_date,
        description: expense.description,
        amount: expense.amount,
        amortization_start_date: expense.amortization_start_date,
        amortization_end_date: expense.amortization_end_date,
        category: expense.category,
        trip: expense.trip,
        payment_method: expense.payment_method,
        is_expense: expense.is_expense,
        currency: expense.currency,
      }
      if (expense.shared_expense) {
        // The amount of a shared expense is edited as the total shared
        newExpense.value.amount = Number(expense.shared_expense.total_amount)
        newExpense.value.currency = expense.shared_expense.currency
        selectedFriendIds.value = expense.shared_expense.participants
          .filter((participant) => participant.id !== expense.shared_expense_participant)
          .map((participant) => participant.user_id)
        loadSplit(expense.shared_expense.participants, newExpense.value.amount)
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
  <p v-if="editingShared" class="mb-3">
    This expense is shared: changing the total amount, the currency, the people or the split updates
    everyone's share, and they are notified. Your quota is {{ myParticipant?.quota }}.
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
      <label for="amount">{{ isSharing ? 'Total amount' : 'Amount' }}</label>
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

    <div>
      <label for="payment-method">Payment Method</label>
      <select
        class="select input input-border w-full"
        id="payment-method"
        v-model="newExpense.payment_method"
      >
        <option :value="null">Select a payment method</option>
        <option
          v-for="paymentMethod in activePaymentMethods"
          :key="paymentMethod.id"
          :value="paymentMethod.id"
        >
          {{ paymentMethod.name }}
        </option>
      </select>
    </div>
    <div v-if="canShare">
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
    <SplitPanel
      v-if="canShare && isSharing && myUserId !== null"
      class="col-span-full"
      v-model:mode="splitMode"
      v-model:quotas="customQuotas"
      :total="Number(newExpense.amount)"
      :currencySymbol="currencySymbol"
      :participants="splitParticipants"
      :creatorId="creatorId!"
      :error="customSplitError"
    />
    <button
      type="submit"
      :disabled="isSubmitting || !!customSplitError"
      class="btn btn-primary col-span-full"
    >
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
