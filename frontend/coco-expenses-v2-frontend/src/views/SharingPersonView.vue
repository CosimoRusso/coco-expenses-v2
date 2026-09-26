<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import apiFetch from '@/utils/apiFetch'
import { formatMovement, movementClass } from '@/utils/movements'
import type { Balances, Movement, MovementsPage } from '@/interfaces/Balance'

const route = useRoute()
const personId = Number(route.params.personId)

const isLoading = ref(true)
const loadError = ref('')
const balances = ref<Balances | null>(null)
const movements = ref<Movement[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const hasNextPage = ref(false)
const hasPreviousPage = ref(false)

const balance = computed(() => balances.value?.balances.find((b) => b.user_id === personId))

async function fetchBalances() {
  const response = await apiFetch('/expenses/balances/')
  if (!response.ok) {
    throw new Error('Failed to load balances.')
  }
  balances.value = await response.json()
}

async function fetchMovements() {
  const response = await apiFetch(
    `/expenses/balances/${personId}/movements/?page=${currentPage.value}`,
  )
  if (!response.ok) {
    throw new Error('Failed to load shared expenses.')
  }
  const page: MovementsPage = await response.json()
  movements.value = page.results
  totalCount.value = page.count
  hasNextPage.value = page.next !== null
  hasPreviousPage.value = page.previous !== null
}

async function load(loaders: Array<() => Promise<void>>) {
  isLoading.value = true
  try {
    await Promise.all(loaders.map((loader) => loader()))
  } catch (error) {
    console.error('Error fetching shared expenses:', error)
    loadError.value = 'Failed to load shared expenses.'
  } finally {
    isLoading.value = false
  }
}

function goToPage(page: number) {
  currentPage.value = page
  load([fetchMovements])
}

function formatBalance(amount: string): string {
  const absolute = Math.abs(Number(amount)).toFixed(2)
  return `${balances.value!.currency.symbol} ${absolute}`
}

function balanceStatus(amount: string): { text: string; class: string } {
  const value = Number(amount)
  if (value > 0) return { text: 'owes you', class: 'text-success' }
  if (value < 0) return { text: 'you owe', class: 'text-error' }
  return { text: 'settled', class: 'text-base-content/60' }
}

onMounted(() => load([fetchBalances, fetchMovements]))
</script>

<template>
  <RouterLink :to="{ name: 'sharing' }" class="link link-hover text-sm">← Sharing</RouterLink>
  <div v-if="loadError" class="text-error my-4">{{ loadError }}</div>
  <template v-else-if="balances">
    <template v-if="balance">
      <h1 class="text-2xl font-bold mt-2 mb-2">{{ balance.first_name }} {{ balance.last_name }}</h1>
      <p class="mb-8 font-semibold" :class="balanceStatus(balance.amount).class">
        {{ balanceStatus(balance.amount).text }}
        <template v-if="Number(balance.amount) !== 0">{{ formatBalance(balance.amount) }}</template>
      </p>
    </template>
    <p v-else-if="!isLoading" class="mt-4">You have no shared expenses with this person.</p>
  </template>
  <div v-if="!loadError && totalCount > 0" class="overflow-x-auto">
    <table class="table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Description</th>
          <th class="text-right">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(movement, index) in movements" :key="index">
          <td class="whitespace-nowrap">{{ movement.date }}</td>
          <td>{{ movement.description }}</td>
          <td class="text-right whitespace-nowrap" :class="movementClass(movement)">
            {{ formatMovement(movement) }}
          </td>
        </tr>
      </tbody>
    </table>
    <div class="flex items-center justify-between mt-4">
      <div class="text-sm text-base-content/60">{{ totalCount }} shared expenses</div>
      <div class="flex items-center gap-2">
        <button
          class="btn btn-sm"
          :disabled="!hasPreviousPage || isLoading"
          @click="goToPage(currentPage - 1)"
        >
          Previous
        </button>
        <span class="text-sm">Page {{ currentPage }}</span>
        <button
          class="btn btn-sm"
          :disabled="!hasNextPage || isLoading"
          @click="goToPage(currentPage + 1)"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>
