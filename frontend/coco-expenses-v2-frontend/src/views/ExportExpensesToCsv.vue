<script setup lang="ts">
import apiFetch from '@/utils/apiFetch'
import { ref } from 'vue'

const loading = ref<boolean>(false)
const errorMsg = ref<string>('')

async function downloadCsv() {
  loading.value = true
  errorMsg.value = ''
  try {
    const response = await apiFetch('/expenses/expenses/download_csv', { method: 'GET' })
    if (!response.ok) {
      console.error(response)
      throw new Error()
    }
    let filename = 'export.csv'
    const disposition = response.headers.get('content-disposition')
    if (disposition && disposition.includes('filename=')) {
      filename = disposition.split('filename=')[1].replace(/["']/g, '')
    }

    const blob = await response.blob()

    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(downloadUrl)
  } catch (error) {
    console.error(error)
    errorMsg.value = 'Unexpected error, cannot download file'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container mx-auto px-4">
    <h1 class="text-3xl font-bold">Export to csv</h1>
    <button @click="downloadCsv" class="btn w-full">Download CSV</button>
  </div>
</template>
