<script setup lang="ts">
import { computed } from 'vue'

export interface MultiSelectOption {
  value: number
  label: string
  disabled?: boolean
}

const props = defineProps<{
  id: string
  options: MultiSelectOption[]
  placeholder: string
  emptyText: string
}>()

const selected = defineModel<number[]>({ required: true })

const summary = computed(() => {
  const labels = props.options
    .filter((option) => selected.value.includes(option.value))
    .map((option) => option.label)
  return labels.length ? labels.join(', ') : props.placeholder
})
</script>

<template>
  <!-- The dropdown stays open while focus is inside it, so it closes on an outside click -->
  <div class="dropdown w-full">
    <div
      :id="id"
      tabindex="0"
      role="button"
      class="select input-border w-full"
      :class="{ 'text-base-content/50': !selected.length }"
    >
      <span class="truncate">{{ summary }}</span>
    </div>
    <ul
      tabindex="-1"
      class="dropdown-content menu bg-base-100 rounded-box z-[1] mt-1 w-full p-2 shadow"
    >
      <li v-if="!options.length" class="menu-disabled">
        <span>{{ emptyText }}</span>
      </li>
      <li v-for="option in options" :key="option.value">
        <label>
          <input
            type="checkbox"
            class="checkbox checkbox-sm"
            :value="option.value"
            :disabled="option.disabled"
            v-model="selected"
          />
          {{ option.label }}
        </label>
      </li>
    </ul>
  </div>
</template>
