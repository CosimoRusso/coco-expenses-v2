<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import apiFetch from '@/utils/apiFetch.ts'
import { dateFromIsoString, dateToISOString } from '@/utils/dateUtils.ts'

interface CategoryStatistics {
  category: { id: number; code: string; name: string; for_expense: boolean }
  actual_amount: string
  forecast_amount: string
}

const startDate = ref<Date | null>(null)
const endDate = ref<Date | null>(null)
const errorMessage = ref<string | null>(null)
const categoryStatistics = ref<CategoryStatistics[]>([])

onMounted(() => {
  // Initialize date inputs to today's date
  const _startDate = new Date()
  _startDate.setMonth(_startDate.getMonth() - 2)
  startDate.value = _startDate
  const _endDate = new Date()
  _endDate.setMonth(_endDate.getMonth() + 1)
  endDate.value = _endDate

  fetchCategoryStatistics().then(() => {})
})

const startDateStr = computed(() => {
  if (!startDate.value) return ''
  return dateToISOString(startDate.value)
})

const endDateStr = computed(() => {
  if (!endDate.value) return ''
  return dateToISOString(endDate.value)
})

async function fetchCategoryStatistics() {
  if (!startDate.value || !endDate.value) {
    errorMessage.value = 'Please select both start and end dates.'
    return
  }
  try {
    errorMessage.value = null
    const response = await apiFetch(
      `/api/expenses/statistics/expense_categories/?start_date=${startDateStr.value}&end_date=${endDateStr.value}`,
    )
    if (!response.ok) {
      errorMessage.value = 'Network response was not ok'
    }
    categoryStatistics.value = await response.json()
  } catch (error) {
    errorMessage.value = 'Error fetching category statistics'
    console.error('Error fetching category statistics:', error)
  }
}

async function fetchStatistics() {
  await fetchCategoryStatistics()
}
</script>

<template>
  <div class="statistics">
    <h1>Statistics</h1>
    <p>This is the statistics page</p>
  </div>
  <div class="filter">
    <label for="dateRange">Date Range:</label>
    <input
      type="date"
      id="startDate"
      name="startDate"
      @change="(e) => (startDate = dateFromIsoString((e.target as HTMLInputElement).value))"
      :value="startDateStr"
    />
    <input
      type="date"
      id="endDate"
      name="endDate"
      @change="(e) => (endDate = dateFromIsoString((e.target as HTMLInputElement).value))"
      :value="endDateStr"
    />
    <button @click="fetchStatistics">Filter</button>
  </div>
  <p class="error-message">{{ errorMessage }}</p>
  <div>
    <h2>Results per Category</h2>
    <div>
      <table id="categoryStatisticsTable">
        <thead>
          <tr>
            <th>Category</th>
            <th>Actual Amount</th>
            <th>Forecast Amount</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stat in categoryStatistics" :key="stat.category.id">
            <td>{{ stat.category.name }}</td>
            <td>{{ stat.actual_amount }}</td>
            <td>{{ stat.forecast_amount }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.statistics {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  margin-bottom: 1.5rem;
}
.error-message {
  color: red;
  font-weight: bold;
}
#categoryStatisticsTable {
  max-width: 500px;
}
</style>
