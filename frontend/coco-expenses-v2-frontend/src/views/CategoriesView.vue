<script setup lang="ts">
import apiFetch from '@/utils/apiFetch'
import { onMounted, ref } from 'vue'

interface Category {
  id: number
  name: string
  code: string
  for_expense: boolean
}

const newCategory = ref<Category>({
  id: 0,
  name: '',
  code: '',
  for_expense: true,
})

const createCategoryError = ref<string>('')
const categories = ref<Category[]>([])
const fetchCategoriesError = ref<string>('')

async function fetchCategories() {
  fetchCategoriesError.value = ''
  const response = await apiFetch('/expenses/expense-categories/?ordering=code')
  if (response.ok) {
    categories.value = await response.json()
  } else {
    const errorData = await response.json()
    fetchCategoriesError.value = errorData?.detail || 'Failed to fetch categories.'
  }
}

async function addCategory() {
  const response = await apiFetch('/expenses/expense-categories/', {
    method: 'POST',
    body: JSON.stringify(newCategory.value),
  })
  if (response.ok) {
    createCategoryError.value = ''
    newCategory.value = {
      id: 0,
      name: '',
      code: '',
      for_expense: true,
    }
    await fetchCategories()
  } else {
    const errorData = await response.json()
    createCategoryError.value = errorData?.detail || 'Failed to create category.'
  }
}

onMounted(() => {
  fetchCategories().then(() => {})
})
</script>

<template>
  <h1 class="text-2xl font-bold mb-8">Categories</h1>
  <h2 class="text-xl font-bold mb-3">Add Category</h2>
  <form
    class="form grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    @submit.prevent="addCategory"
  >
    <div>
      <label for="name">Name</label>
      <input
        type="text"
        id="name"
        class="input input-border w-full"
        v-model="newCategory.name"
        required
      />
    </div>
    <div>
      <label for="code">Code</label>
      <input
        type="text"
        id="code"
        class="input input-border w-full"
        v-model="newCategory.code"
        required
      />
    </div>
    <div>
      <label for="for_expense" class="flex items-center gap-2">
        <input
          type="checkbox"
          id="for_expense"
          class="checkbox"
          v-model="newCategory.for_expense"
        />
        For Expense
      </label>
    </div>
    <div class="col-span-full">
      <button type="submit" class="btn btn-primary">Add Category</button>
    </div>
  </form>
  <div v-if="createCategoryError" class="text-red-50 my-4">{{ createCategoryError }}</div>
  <h2 class="text-xl font-bold mb-3 my-8">Categories List</h2>
  <div class="overflow-x-auto">
    <table class="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Code</th>
          <th>For Expense</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="categories.length === 0">
          <td colspan="3" class="no-data">No categories found</td>
        </tr>
        <tr v-for="category in categories" :key="category.id">
          <td>{{ category.name }}</td>
          <td>{{ category.code }}</td>
          <td>{{ category.for_expense }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div v-if="fetchCategoriesError" class="text-red-50 my-4">{{ fetchCategoriesError }}</div>
</template>
