<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import apiFetch from '@/utils/apiFetch'
import type { Currency } from '@/interfaces/Currency'
import type { Notification } from '@/interfaces/Notification'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const notificationStore = useNotificationStore()

const isLoading = ref(true)
const notifications = ref<Notification[]>([])
const currencies = ref<Currency[]>([])
const loadError = ref('')

onMounted(async () => {
  try {
    await Promise.all([fetchNotifications(), fetchCurrencies()])
  } finally {
    isLoading.value = false
  }
})

async function fetchNotifications() {
  const response = await apiFetch('/expenses/notifications/')
  if (response.ok) {
    notifications.value = await response.json()
  } else {
    loadError.value = 'Failed to load notifications.'
  }
}

async function fetchCurrencies() {
  const response = await apiFetch('/expenses/currencies/')
  if (response.ok) {
    currencies.value = await response.json()
  }
}

function currencySymbol(currencyId: number): string {
  return currencies.value.find((currency) => currency.id === currencyId)?.symbol ?? ''
}

function title(notification: Notification): string {
  const sharedExpense = notification.shared_expense
  if (notification.kind === 'SHARED_EXPENSE_REQUESTED' && sharedExpense) {
    return `${sharedExpense.created_by} shared "${sharedExpense.description}" with you`
  }
  return 'Notification'
}

async function markRead(notification: Notification) {
  if (notification.read_at) {
    return
  }
  const updated = await notificationStore.markRead(notification.id)
  if (updated) {
    notification.read_at = updated.read_at
  }
}

async function completeSharedExpense(notification: Notification) {
  await markRead(notification)
  router.push({ name: 'expenses', query: { notification: notification.id } })
}
</script>

<template>
  <h1 class="text-2xl font-bold mb-8">Notifications</h1>
  <div v-if="loadError" class="text-error my-4">{{ loadError }}</div>
  <p v-else-if="!isLoading && !notifications.length">No notifications yet.</p>
  <ul class="flex flex-col gap-3">
    <li
      v-for="notification in notifications"
      :key="notification.id"
      class="card card-border bg-base-100 cursor-pointer"
      :class="{ 'bg-base-200': !notification.read_at }"
      @click="markRead(notification)"
    >
      <div class="card-body p-4 flex-row items-center gap-4">
        <span
          class="status"
          :class="notification.read_at ? 'invisible' : 'status-error'"
          :aria-label="notification.read_at ? undefined : 'Unread'"
        ></span>
        <div class="flex-1">
          <p :class="{ 'font-semibold': !notification.read_at }">{{ title(notification) }}</p>
          <p v-if="notification.shared_expense" class="text-sm">
            Your quota: {{ currencySymbol(notification.shared_expense.currency) }}
            {{ notification.shared_expense.quota }} of
            {{ currencySymbol(notification.shared_expense.currency) }}
            {{ notification.shared_expense.total_amount }}
          </p>
          <p class="text-xs text-base-content/60">
            {{ new Date(notification.created_at).toLocaleString() }}
          </p>
        </div>
        <template v-if="notification.shared_expense">
          <span v-if="notification.shared_expense.is_completed" class="badge badge-success">
            Completed
          </span>
          <button
            v-else
            type="button"
            class="btn btn-primary btn-sm"
            @click.stop="completeSharedExpense(notification)"
          >
            Complete expense
          </button>
        </template>
      </div>
    </li>
  </ul>
</template>
