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
  const modification = notification.modification
  if (notification.kind === 'SHARED_EXPENSE_MODIFIED' && modification) {
    return `${modification.modified_by} modified "${modification.description}"`
  }
  const deletion = notification.deletion
  if (notification.kind === 'SHARED_EXPENSE_DELETED' && deletion) {
    return `${deletion.deleted_by} deleted "${deletion.description}"`
  }
  return 'Notification'
}

function changes(notification: Notification): string[] {
  const deletion = notification.deletion
  if (deletion) {
    return [
      `Total: ${currencySymbol(deletion.currency)} ${deletion.amount}. It was deleted for you too.`,
    ]
  }
  const modification = notification.modification
  if (!modification) {
    return []
  }
  const lines: string[] = []
  const totalBefore = `${currencySymbol(modification.currency_before)} ${modification.amount_before}`
  const totalAfter = `${currencySymbol(modification.currency_after)} ${modification.amount_after}`
  if (totalBefore !== totalAfter) {
    lines.push(`Total: ${totalBefore} → ${totalAfter}`)
  }
  const { number_participants_before: before, number_participants_after: after } = modification
  if (before !== after) {
    lines.push(`People sharing it: ${before} → ${after}`)
  }
  if (modification.you_were_added) lines.push('You were added')
  if (modification.you_were_removed) lines.push('You were removed')
  return lines
}

// A completed share of a modified expense is updated by saving the expense again
function canUpdateExpense(notification: Notification): boolean {
  return (
    notification.kind === 'SHARED_EXPENSE_MODIFIED' && !!notification.shared_expense?.expense_id
  )
}

async function updateExpense(notification: Notification) {
  await markRead(notification)
  router.push({ name: 'expenses', query: { edit: notification.shared_expense!.expense_id } })
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
          <p v-for="change in changes(notification)" :key="change" class="text-sm">
            {{ change }}
          </p>
          <p class="text-xs text-base-content/60">
            {{ new Date(notification.created_at).toLocaleString() }}
          </p>
        </div>
        <template v-if="notification.shared_expense">
          <button
            v-if="canUpdateExpense(notification)"
            type="button"
            class="btn btn-primary btn-sm"
            @click.stop="updateExpense(notification)"
          >
            Update my expense
          </button>
          <span v-else-if="notification.shared_expense.is_completed" class="badge badge-success">
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
