<script setup lang="ts">
import { computed } from 'vue'
import {
  fromCents,
  remainingCents,
  splitEqually,
  toCents,
  type Quotas,
  type SplitMode,
} from '@/utils/split'

export interface SplitParticipant {
  userId: number
  label: string
}

const props = defineProps<{
  total: number
  currencySymbol: string
  // Who shares the expense, shown in this order
  participants: SplitParticipant[]
  // The creator of the shared expense, who takes the leftover cents of an equal split
  creatorId: number
  // Why the quotas cannot be saved, or ''
  error: string
}>()

const mode = defineModel<SplitMode>('mode', { required: true })
const quotas = defineModel<Quotas>('quotas', { required: true })

// The creator first, as the backend expects them when checking and splitting
const userIds = computed(() => {
  const ids = props.participants.map((participant) => participant.userId)
  return [props.creatorId, ...ids.filter((id) => id !== props.creatorId)]
})
const equalQuotas = computed(() => splitEqually(props.total, userIds.value))
const shownQuotas = computed(() => (mode.value === 'equally' ? equalQuotas.value : quotas.value))
const remaining = computed(() => remainingCents(props.total, quotas.value, userIds.value))

// Switching to amounts starts from the equal split, to adjust from there
function selectMode(selected: SplitMode) {
  if (selected === 'amount' && mode.value === 'equally') {
    quotas.value = { ...equalQuotas.value }
  }
  mode.value = selected
}

function fillRest(userId: number) {
  quotas.value[userId] = fromCents(toCents(quotas.value[userId]) + remaining.value)
}
</script>

<template>
  <div class="rounded-box border border-base-300 p-4">
    <div class="flex items-center justify-between mb-3">
      <span class="font-semibold">Split</span>
      <div class="join">
        <button
          type="button"
          class="btn btn-sm join-item"
          :class="{ 'btn-active btn-primary': mode === 'equally' }"
          @click="selectMode('equally')"
        >
          Equally
        </button>
        <button
          type="button"
          class="btn btn-sm join-item"
          :class="{ 'btn-active btn-primary': mode === 'amount' }"
          @click="selectMode('amount')"
        >
          By amount
        </button>
      </div>
    </div>

    <div
      v-for="participant in participants"
      :key="participant.userId"
      class="flex items-center gap-3 py-1"
    >
      <label :for="`quota-${participant.userId}`" class="flex-1 truncate">
        {{ participant.label }}
      </label>
      <button
        v-if="mode === 'amount' && remaining > 0"
        type="button"
        class="btn btn-ghost btn-xs"
        @click="fillRest(participant.userId)"
      >
        Fill rest
      </button>
      <input
        :id="`quota-${participant.userId}`"
        type="number"
        step="0.01"
        min="0"
        class="input input-border input-sm w-32 text-right"
        :disabled="mode === 'equally'"
        :value="shownQuotas[participant.userId]"
        @input="quotas[participant.userId] = ($event.target as HTMLInputElement).value"
      />
      <span class="w-6">{{ currencySymbol }}</span>
    </div>

    <div class="border-t border-base-300 mt-2 pt-2 text-sm">
      <span v-if="error" class="text-error">{{ error }}</span>
      <span v-else class="text-success">
        {{ fromCents(toCents(total)) }} of {{ fromCents(toCents(total)) }} {{ currencySymbol }} ✓
      </span>
    </div>
  </div>
</template>
