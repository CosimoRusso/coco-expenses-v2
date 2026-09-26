<script setup lang="ts">
import { computed } from 'vue'
import type { Expense } from '@/interfaces/Expense'
import type { SharedExpenseParticipant } from '@/interfaces/SharedExpense'

const MAX_AVATARS = 2

const props = defineProps<{
  expense: Expense
}>()

// The people the expense is shared with, without the current user
const others = computed(() =>
  (props.expense.shared_expense?.participants ?? []).filter(
    (participant) => participant.id !== props.expense.shared_expense_participant,
  ),
)
// Up to MAX_AVATARS people; with more, only the first one followed by a counter of the rest
const shown = computed(() =>
  others.value.length > MAX_AVATARS ? others.value.slice(0, 1) : others.value,
)
const hiddenCount = computed(() => others.value.length - shown.value.length)
const description = computed(
  () =>
    `Shared with ${others.value.map((other) => `${other.first_name} ${other.last_name}`).join(', ')}`,
)

function initials(participant: SharedExpenseParticipant): string {
  return `${participant.first_name.charAt(0)}${participant.last_name.charAt(0)}`.toUpperCase()
}
</script>

<template>
  <div
    v-if="others.length"
    class="avatar-group -space-x-3"
    role="img"
    :title="description"
    :aria-label="description"
  >
    <div v-for="other in shown" :key="other.id" class="avatar avatar-placeholder">
      <div class="bg-neutral text-neutral-content w-7 rounded-full">
        <span class="text-xs">{{ initials(other) }}</span>
      </div>
    </div>
    <div v-if="hiddenCount" class="avatar avatar-placeholder">
      <div class="bg-neutral text-neutral-content w-7 rounded-full">
        <span class="text-xs">+{{ hiddenCount }}</span>
      </div>
    </div>
  </div>
</template>
