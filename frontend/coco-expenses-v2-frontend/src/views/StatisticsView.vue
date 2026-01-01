<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import apiFetch from '@/utils/apiFetch.ts'
import { dateToISOString } from '@/utils/dateUtils.ts'
import { Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import type { Currency } from '@/interfaces/Currency'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
)

interface CategoryStatistics {
  category: { id: number; code: string; name: string; for_expense: boolean }
  currency: Currency
  amount: string
}

interface AmortizationTimelineItem {
  date: string
  expense_amount: string
  non_expense_amount: string
  difference: string
}

const startDateStr = ref<string>('')
const endDateStr = ref<string>('')
const errorMessage = ref<string | null>(null)
const categoryStatistics = ref<CategoryStatistics[]>([])
const amortizationTimeline = ref<AmortizationTimelineItem[]>([])
const currency = ref<Currency | null>(null)

onMounted(() => {
  // Initialize date inputs to today's date
  const _startDate = new Date()
  _startDate.setMonth(_startDate.getMonth() - 2)
  startDateStr.value = dateToISOString(_startDate)
  const _endDate = new Date()
  _endDate.setMonth(_endDate.getMonth() + 1)
  endDateStr.value = dateToISOString(_endDate)

  fetchCategoryStatistics().then(() => {})
  fetchAmortizationTimeline().then(() => {})
})

async function fetchCategoryStatistics() {
  if (!startDateStr.value || !endDateStr.value) {
    errorMessage.value = 'Please select both start and end dates.'
    return
  }
  try {
    errorMessage.value = null
    const response = await apiFetch(
      `/expenses/statistics/expense_categories/?start_date=${startDateStr.value}&end_date=${endDateStr.value}`,
    )
    if (!response.ok) {
      errorMessage.value = 'Network response was not ok'
    }
    categoryStatistics.value = await response.json()
    currency.value = categoryStatistics.value[0].currency
  } catch (error) {
    errorMessage.value = 'Error fetching category statistics'
    console.error('Error fetching category statistics:', error)
  }
}

async function fetchStatistics() {
  await fetchCategoryStatistics()
  await fetchAmortizationTimeline()
}

async function fetchAmortizationTimeline() {
  if (!startDateStr.value || !endDateStr.value) {
    return
  }
  try {
    const response = await apiFetch(
      `/expenses/statistics/amortization_timeline/?start_date=${startDateStr.value}&end_date=${endDateStr.value}`,
    )
    if (response.ok) {
      amortizationTimeline.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching amortization timeline:', error)
  }
}

// Chart data computed property
const chartData = computed(() => {
  if (categoryStatistics.value.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: categoryStatistics.value.map((stat) => stat.category.name),
    datasets: [
      {
        label: 'Amount',
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
        data: categoryStatistics.value.map((stat) => parseFloat(stat.amount) || 0),
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    title: {
      display: true,
      text: 'Amount by Category',
    },
  },
  scales: {
    y: {
      beginAtZero: true,
    },
  },
}

const amortizationChartData = computed(() => {
  if (amortizationTimeline.value.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: amortizationTimeline.value.map((item) => item.date),
    datasets: [
      {
        label: 'Expenses',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        data: amortizationTimeline.value.map((item) => parseFloat(item.expense_amount) || 0),
      },
      {
        label: 'Income',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        data: amortizationTimeline.value.map((item) => parseFloat(item.non_expense_amount) || 0),
      },
      {
        label: 'Difference',
        backgroundColor: 'rgba(255, 159, 64, 0.2)',
        borderColor: 'rgba(255, 159, 64, 1)',
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        data: amortizationTimeline.value.map((item) => parseFloat(item.difference) || 0),
      },
    ],
  }
})

const amortizationChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
    },
    title: {
      display: true,
      text: 'Amortization Timeline',
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      title: {
        display: true,
        text: 'Amount',
      },
    },
    y: {
      title: {
        display: true,
        text: 'Date',
      },
    },
  },
}
</script>

<template>
  <div class="max-w-5xl mx-auto p-5">
    <h1 class="text-2xl font-bold mb-6">Statistics{{ currency?.display_name }}</h1>
    <p class="mb-4">The statistics are displayed in the currency: {{ currency?.display_name }}</p>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
    <div>
      <label for="startDate">Start Date</label>
      <input
        type="date"
        id="startDate"
        name="startDate"
        v-model="startDateStr"
        class="input input-border w-full"
      />
    </div>
    <div>
      <label for="endDate">End Date</label>
      <input
        type="date"
        id="endDate"
        name="endDate"
        v-model="endDateStr"
        class="input input-border w-full"
      />
    </div>
    <div class="flex items-end">
      <button @click="fetchStatistics" class="btn btn-primary w-full">Filter</button>
    </div>
  </div>
  <p v-if="errorMessage" class="text-error font-bold mb-4">{{ errorMessage }}</p>
  <div>
    <h2 class="text-xl font-bold mb-3">Results per Category</h2>
    <div class="flex flex-wrap gap-8 mt-6">
      <div class="flex-1 min-w-[400px] h-[400px] bg-base-100 p-4 rounded-lg shadow">
        <Bar v-if="categoryStatistics.length > 0" :data="chartData" :options="chartOptions" />
        <p v-else class="text-center text-gray-500 p-8">
          No data available for the selected date range
        </p>
      </div>
      <div class="flex-1 min-w-[300px]">
        <div class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="categoryStatistics.length === 0">
                <td colspan="2" class="no-data">No categories found</td>
              </tr>
              <tr v-for="stat in categoryStatistics" :key="stat.category.id">
                <td>{{ stat.category.name }}</td>
                <td>{{ stat.amount }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
  <div>
    <h2 class="text-xl font-bold mb-3 mt-8">Amortization Timeline</h2>
    <div class="w-full h-[400px] bg-base-100 p-4 rounded-lg shadow mt-6">
      <Line
        v-if="amortizationTimeline.length > 0"
        :data="amortizationChartData"
        :options="amortizationChartOptions"
      />
      <p v-else class="text-center text-gray-500 p-8">
        No data available for the selected date range
      </p>
    </div>
  </div>
</template>
