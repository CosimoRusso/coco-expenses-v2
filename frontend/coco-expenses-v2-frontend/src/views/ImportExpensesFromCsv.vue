<template>
  <div class="import-expenses">
    <h1>Importa Spese da CSV</h1>
    <form @submit.prevent="submitCsv" enctype="multipart/form-data">
      <div>
        <label for="csvFile">Seleziona file CSV:</label>
        <input
          type="file"
          id="csvFile"
          ref="csvFile"
          @change="onFileChange"
          accept=".csv"
          required
        />
      </div>
      <button type="submit" :disabled="loading">Carica</button>
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
import axios from 'axios'

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
    const res = await axios.post('/api/expenses/expenses/load_from_csv/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    result.value = res.data
  } catch (e: any) {
    error.value = e.response?.data?.error || "Errore durante l'importazione."
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.import-expenses {
  max-width: 500px;
  margin: 2rem auto;
  padding: 2rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: #fafafa;
}
.error {
  color: red;
  margin-top: 1rem;
}
</style>
