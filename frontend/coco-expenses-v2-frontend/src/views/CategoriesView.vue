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
    const response = await apiFetch('/expenses/expense-categories/')
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
    fetchCategories().then(() => { })
})
</script>

<template>
    <h1>Categories</h1>
    <h2>Add Category</h2>
    <form @submit.prevent="addCategory">
        <div>
            <label for="name">Name</label>
            <input type="text" id="name" v-model="newCategory.name" required />
        </div>
        <div>
            <label for="code">Code</label>
            <input type="text" id="code" v-model="newCategory.code" required />
        </div>
        <div>
            <label for="for_expense">For Expense</label>
            <input type="checkbox" id="for_expense" v-model="newCategory.for_expense" required />
        </div>
        <button type="submit">Add Category</button>
    </form>
    <p v-if="createCategoryError" class="error">{{ createCategoryError }}</p>
    <h2>Categories List</h2>
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Code</th>
                <th>For Expense</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="category in categories" :key="category.id">
                <td>{{ category.name }}</td>
                <td>{{ category.code }}</td>
                <td>{{ category.for_expense }}</td>
            </tr>
        </tbody>
    </table>
    <p v-if="fetchCategoriesError" class="error">{{ fetchCategoriesError }}</p>
</template>

<style scoped>
.error {
    color: red;
    font-weight: bold;
    margin-bottom: 10px;
}
</style>
