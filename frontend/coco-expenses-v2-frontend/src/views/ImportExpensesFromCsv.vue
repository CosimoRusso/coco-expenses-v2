<template>
  <div class="container mx-auto px-4">
    <h1 class="text-3xl font-bold mb-3">Importa Spese da CSV</h1>
    <p>Il file CSV deve contenere le seguenti colonne:</p>
    <p class="font-semibold mb-2 mt-2">
      expense_date, description, amount, amortization_start_date, amortization_end_date, category,
      trip, currency, is_expense
    </p>

    <div
      class="rounded-xl overflow-hidden shadow-lg bg-white border border-gray-100 transition-all hover:shadow-xl p-4 mb-4"
    >
      <p>Esempi di righe valide:</p>
      <ul class="list-disc list-inside space-y-1 text-gray-700">
        <li>
          2025-01-01,Spesa di
          esempio,1034.34,100,2025-01-01,2025-01-01,Categoria_esempio,Viaggio_esempio,EUR,True
        </li>
        <li>
          2025-01-01,Entrata di
          esempio,20.43,11.1,2025-01-01,2025-01-01,Categoria_2,Viaggio_2,USD,False
        </li>
      </ul>
    </div>

    <form @submit.prevent="submitCsv" enctype="multipart/form-data">
      <div class="max-w-md mb-4">
        <label for="csvFile" class="block text-sm font-medium text-gray-700 mb-2"
          >Seleziona file CSV:</label
        >
        <input
          type="file"
          id="csvFile"
          ref="csvFile"
          @change="onFileChange"
          accept=".csv"
          required
          class="block w-full text-sm text-gray-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 file:cursor-pointer file:transition-colors"
        />
      </div>
      <button type="submit" :disabled="loading" class="btn btn-primary w-full">Carica</button>
    </form>
    <div v-if="loading">Caricamento in corso...</div>
    <div v-if="result">
      <h2>Risultato importazione</h2>
      <div>Spese create: {{ result.created }}</div>
      <div v-if="result.errors && result.errors.length">
        <h3>Errori:</h3>
        <ul>
          <li v-for="err in result.errors" :key="err.row">Riga {{ err.row }}: {{ err.error }}</li>
        </ul>
      </div>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import apiFetch from '@/utils/apiFetch'

const csvFile = ref<HTMLInputElement | null>(null)
const loading = ref(false)
const result = ref<any>(null)
const error = ref<string | null>(null)

function onFileChange() {
  error.value = null
  result.value = null
}

async function submitCsv() {
  if (!csvFile.value || !csvFile.value.files || !csvFile.value.files[0]) {
    error.value = 'Seleziona un file CSV.'
    return
  }
  loading.value = true
  error.value = null
  result.value = null
  const formData = new FormData()
  formData.append('file', csvFile.value.files[0])
  try {
    const res = await apiFetch(
      '/expenses/expenses/load_from_csv/',
      {
        method: 'POST',
        body: formData,
      },
      true,
    )
    if (res.ok) {
      result.value = await res.json()
    } else {
      error.value = "Errore durante l'importazione."
    }
  } catch (e: any) {
    error.value = e.response?.data?.error || "Errore durante l'importazione."
  } finally {
    loading.value = false
  }
}
</script>
