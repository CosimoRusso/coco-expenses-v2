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
  <div class="statistics">
    <h1>Statistics</h1>
    <p>This is the statistics page</p>
  </div>
  <div class="filter">
    <label for="dateRange">Date Range:</label>
    <input type="date" id="startDate" name="startDate" v-model="startDateStr" />
    <input type="date" id="endDate" name="endDate" v-model="endDateStr" />
    <button @click="fetchStatistics">Filter</button>
  </div>
  <p class="error-message">{{ errorMessage }}</p>
  <div>
    <h2>Results per Category</h2>
    <div class="statistics-content">
      <div class="chart-container">
        <Bar v-if="categoryStatistics.length > 0" :data="chartData" :options="chartOptions" />
        <p v-else class="no-data-message">No data available for the selected date range</p>
      </div>
      <div class="table-container">
        <table id="categoryStatisticsTable">
          <thead>
            <tr>
              <th>Category</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stat in categoryStatistics" :key="stat.category.id">
              <td>{{ stat.category.name }}</td>
              <td>{{ stat.amount }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <div>
    <h2>Amortization Timeline</h2>
    <div class="chart-container-full">
      <Line
        v-if="amortizationTimeline.length > 0"
        :data="amortizationChartData"
        :options="amortizationChartOptions"
      />
      <p v-else class="no-data-message">No data available for the selected date range</p>
    </div>
  </div>
</template>

<style scoped>
.statistics {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  margin-bottom: 1.5rem;
}

.error-message {
  color: red;
  font-weight: bold;
}

.statistics-content {
  display: flex;
  gap: 2rem;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}

.chart-container {
  flex: 1;
  min-width: 400px;
  height: 400px;
  background-color: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.table-container {
  flex: 1;
  min-width: 300px;
}

#categoryStatisticsTable {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

#categoryStatisticsTable thead {
  background-color: #f5f5f5;
}

#categoryStatisticsTable th,
#categoryStatisticsTable td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

#categoryStatisticsTable th {
  font-weight: bold;
}

.no-data-message {
  text-align: center;
  color: #999;
  padding: 2rem;
}

.chart-container-full {
  width: 100%;
  height: 400px;
  background-color: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 1.5rem;
}
</style>
