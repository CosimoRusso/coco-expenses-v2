<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import apiFetch from '@/utils/apiFetch'
import type { Currency } from '@/interfaces/Currency'
import type { Notification } from '@/interfaces/Notification'
import type { PaginatedResponse } from '@/interfaces/PaginatedResponse'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const notificationStore = useNotificationStore()

const isLoading = ref(true)
const notifications = ref<Notification[]>([])
const currencies = ref<Currency[]>([])
const loadError = ref('')
const nextPage = ref<number | null>(1)
const isLoadingMore = ref(false)
const listEnd = ref<HTMLElement | null>(null)

const listEndObserver = new IntersectionObserver(onListEndVisibilityChange, {
  rootMargin: '200px',
})

onMounted(async () => {
  try {
    await Promise.all([fetchNextPage(), fetchCurrencies()])
  } finally {
    isLoading.value = false
  }
  watchListEnd()
})

onUnmounted(() => listEndObserver.disconnect())

function canLoadMore(): boolean {
  return nextPage.value !== null && !loadError.value
}

// The observer reports only changes of visibility, so observing again is what makes it
// report a list end that is still in view after a page has been appended.
function watchListEnd() {
  listEndObserver.disconnect()
  if (canLoadMore() && listEnd.value) {
    listEndObserver.observe(listEnd.value)
  }
}

async function onListEndVisibilityChange(entries: IntersectionObserverEntry[]) {
  const isListEndVisible = entries.some((entry) => entry.isIntersecting)
  if (!isListEndVisible || isLoadingMore.value) {
    return
  }
  isLoadingMore.value = true
  try {
    await fetchNextPage()
  } finally {
    isLoadingMore.value = false
  }
  watchListEnd()
}

async function fetchNextPage() {
  const page = nextPage.value
  if (page === null) {
    return
  }
  const response = await apiFetch(`/expenses/notifications/?page=${page}`)
  if (!response.ok) {
    loadError.value = 'Failed to load notifications.'
    return
  }
  const data: PaginatedResponse<Notification> = await response.json()
  appendNotifications(data.results)
  nextPage.value = data.next ? page + 1 : null
}

// A notification created between two requests shifts the pages by one, so the next page
// starts with a notification that is already listed.
function appendNotifications(page: Notification[]) {
  const listedIds = new Set(notifications.value.map((notification) => notification.id))
  const unlisted = page.filter((notification) => !listedIds.has(notification.id))
  notifications.value.push(...unlisted)
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
  <p v-if="!isLoading && !loadError && !notifications.length">No notifications yet.</p>
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
  <div ref="listEnd" class="flex justify-center my-4">
    <span v-if="isLoadingMore" class="loading loading-spinner" aria-label="Loading more"></span>
  </div>
  <div v-if="loadError" class="text-error my-4">{{ loadError }}</div>
</template>
