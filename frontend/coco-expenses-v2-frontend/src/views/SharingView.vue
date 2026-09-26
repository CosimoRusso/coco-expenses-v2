<script setup lang="ts">
import { onMounted, ref } from 'vue'
import apiFetch from '@/utils/apiFetch'
import type { Balance, Balances, Movement } from '@/interfaces/Balance'

const isLoading = ref(true)
const balances = ref<Balances | null>(null)
const loadError = ref('')

onMounted(async () => {
  try {
    const response = await apiFetch('/expenses/balances/')
    if (!response.ok) {
      throw new Error('Failed to load balances.')
    }
    balances.value = await response.json()
  } catch (error) {
    console.error('Error fetching balances:', error)
    loadError.value = 'Failed to load balances.'
  } finally {
    isLoading.value = false
  }
})

function formatAmount(amount: string): string {
  const absolute = Math.abs(Number(amount)).toFixed(2)
  return `${balances.value!.currency.symbol} ${absolute}`
}

function formatMovementAmount(movement: Movement): string {
  const absolute = Math.abs(Number(movement.amount)).toFixed(2)
  return `${movement.currency.symbol} ${absolute}`
}

function movementClass(movement: Movement): string {
  return Number(movement.amount) < 0 ? 'text-error' : 'text-success'
}

function status(balance: Balance): { text: string; class: string } {
  const amount = Number(balance.amount)
  if (amount > 0) return { text: 'owes you', class: 'text-success' }
  if (amount < 0) return { text: 'you owe', class: 'text-error' }
  return { text: 'settled', class: 'text-base-content/60' }
}
</script>

<template>
  <h1 class="text-2xl font-bold mb-8">Sharing</h1>
  <div v-if="loadError" class="text-error my-4">{{ loadError }}</div>
  <template v-else-if="!isLoading && balances">
    <p v-if="!balances.balances.length">You have no shared expenses yet.</p>
    <div v-else class="overflow-x-auto">
      <p class="text-sm text-base-content/60 mb-3">
        Balances in {{ balances.currency.display_name }}
      </p>
      <table class="table">
        <thead>
          <tr>
            <th>Person</th>
            <th></th>
            <th class="text-right">Balance</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="balance in balances.balances" :key="balance.user_id">
            <tr class="border-b-0">
              <td>{{ balance.first_name }} {{ balance.last_name }}</td>
              <td :class="status(balance).class">{{ status(balance).text }}</td>
              <td class="text-right font-semibold" :class="status(balance).class">
                {{ formatAmount(balance.amount) }}
              </td>
            </tr>
            <tr>
              <td colspan="3" class="pt-0">
                <ul class="text-sm text-base-content/70 pl-4">
                  <li
                    v-for="(movement, index) in balance.movements"
                    :key="index"
                    class="flex gap-4 py-0.5"
                  >
                    <span class="text-base-content/50 whitespace-nowrap">{{ movement.date }}</span>
                    <span class="grow">{{ movement.description }}</span>
                    <span class="whitespace-nowrap" :class="movementClass(movement)">
                      {{ Number(movement.amount) < 0 ? '−' : '+' }}
                      {{ formatMovementAmount(movement) }}
                    </span>
                  </li>
                </ul>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </template>
</template>
