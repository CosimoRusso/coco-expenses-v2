<script setup lang="ts">
import apiFetch from '@/utils/apiFetch'
import { onMounted, ref } from 'vue'
import EditIcon from '../../icons/EditIcon.vue'
import DeleteIcon from '../../icons/DeleteIcon.vue'
import type { PaymentMethod } from '@/interfaces/PaymentMethod'

function emptyPaymentMethod(): PaymentMethod {
  return { id: 0, code: '', name: '', is_active: true }
}

const newPaymentMethod = ref<PaymentMethod>(emptyPaymentMethod())
const paymentMethods = ref<PaymentMethod[]>([])
const saveError = ref<string>('')
const fetchError = ref<string>('')
const deleteError = ref<string>('')
const editingId = ref<number | null>(null)

function errorMessage(errorData: Record<string, unknown> | null, fallback: string): string {
  if (!errorData) return fallback
  if (typeof errorData.detail === 'string') return errorData.detail
  const fieldErrors = Object.values(errorData).flat()
  return fieldErrors.length > 0 ? String(fieldErrors[0]) : fallback
}

async function fetchPaymentMethods() {
  fetchError.value = ''
  const response = await apiFetch('/expenses/payment-methods/')
  if (response.ok) {
    paymentMethods.value = await response.json()
  } else {
    fetchError.value = errorMessage(await response.json(), 'Failed to fetch payment methods.')
  }
}

async function savePaymentMethod() {
  saveError.value = ''
  const url = editingId.value
    ? `/expenses/payment-methods/${editingId.value}/`
    : '/expenses/payment-methods/'
  const response = await apiFetch(url, {
    method: editingId.value ? 'PUT' : 'POST',
    body: JSON.stringify(newPaymentMethod.value),
  })

  if (!response.ok) {
    const fallback = editingId.value
      ? 'Failed to update payment method.'
      : 'Failed to create payment method.'
    saveError.value = errorMessage(await response.json(), fallback)
    return
  }
  editingId.value = null
  newPaymentMethod.value = emptyPaymentMethod()
  await fetchPaymentMethods()
}

function editPaymentMethod(paymentMethod: PaymentMethod) {
  editingId.value = paymentMethod.id
  newPaymentMethod.value = { ...paymentMethod }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editingId.value = null
  newPaymentMethod.value = emptyPaymentMethod()
}

async function deletePaymentMethod(paymentMethodId: number) {
  if (!confirm('Are you sure you want to delete this payment method?')) {
    return
  }

  deleteError.value = ''
  try {
    const response = await apiFetch(`/expenses/payment-methods/${paymentMethodId}/`, {
      method: 'DELETE',
    })
    if (response.ok) {
      await fetchPaymentMethods()
    } else {
      deleteError.value = errorMessage(await response.json(), 'Failed to delete payment method.')
    }
  } catch (error) {
    console.error('Error deleting payment method:', error)
    deleteError.value = 'Failed to delete payment method.'
  }
}

onMounted(() => {
  fetchPaymentMethods()
})
</script>

<template>
  <h1 class="text-2xl font-bold mb-8">Payment Methods</h1>
  <h2 class="text-xl font-bold mb-3">
    {{ editingId ? 'Edit Payment Method' : 'Add Payment Method' }}
  </h2>
  <form
    class="form grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    @submit.prevent="savePaymentMethod"
  >
    <div>
      <label for="name">Name</label>
      <input
        type="text"
        id="name"
        class="input input-border w-full"
        v-model="newPaymentMethod.name"
        required
      />
    </div>
    <div>
      <label for="code">Code</label>
      <input
        type="text"
        id="code"
        class="input input-border w-full"
        v-model="newPaymentMethod.code"
        required
      />
    </div>
    <div>
      <label for="is_active" class="flex items-center gap-2">
        <input
          type="checkbox"
          id="is_active"
          class="checkbox"
          v-model="newPaymentMethod.is_active"
        />
        Is Active
      </label>
    </div>
    <div class="col-span-full flex gap-2">
      <button type="submit" class="btn btn-primary">
        {{ editingId ? 'Update' : 'Add Payment Method' }}
      </button>
      <button v-if="editingId" type="button" @click="cancelEdit" class="btn btn-secondary">
        Cancel
      </button>
    </div>
  </form>
  <div v-if="saveError" class="text-red-50 my-4">{{ saveError }}</div>
  <h2 class="text-xl font-bold mb-3 my-8">Payment Methods List</h2>
  <div v-if="deleteError" class="text-red-50 my-4">{{ deleteError }}</div>
  <div class="overflow-x-auto">
    <table class="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Code</th>
          <th>Is Active</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="paymentMethods.length === 0">
          <td colspan="4" class="no-data">No payment methods found</td>
        </tr>
        <tr v-for="paymentMethod in paymentMethods" :key="paymentMethod.id">
          <td>{{ paymentMethod.name }}</td>
          <td>{{ paymentMethod.code }}</td>
          <td>{{ paymentMethod.is_active }}</td>
          <td>
            <div class="flex gap-2">
              <button
                @click="editPaymentMethod(paymentMethod)"
                title="Edit"
                style="background: none; border: none; cursor: pointer"
              >
                <EditIcon />
              </button>
              <button
                @click="deletePaymentMethod(paymentMethod.id)"
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
  <div v-if="fetchError" class="text-red-50 my-4">{{ fetchError }}</div>
</template>
