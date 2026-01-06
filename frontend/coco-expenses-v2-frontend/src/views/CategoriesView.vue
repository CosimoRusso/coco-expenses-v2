<script setup lang="ts">
import apiFetch from '@/utils/apiFetch'
import { onMounted, ref } from 'vue'
import EditIcon from '../../icons/EditIcon.vue'
import DeleteIcon from '../../icons/DeleteIcon.vue'

interface Category {
  id: number
  name: string
  code: string
  for_expense: boolean
  is_active: boolean
}

const newCategory = ref<Category>({
  id: 0,
  name: '',
  code: '',
  for_expense: true,
  is_active: true,
})

const createCategoryError = ref<string>('')
const categories = ref<Category[]>([])
const fetchCategoriesError = ref<string>('')
const deleteCategoryError = ref<string>('')
const editingId = ref<number | null>(null)

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
  createCategoryError.value = ''
  let response: Response
  
  if (editingId.value) {
    // Update existing category
    response = await apiFetch(`/expenses/expense-categories/${editingId.value}/`, {
      method: 'PUT',
      body: JSON.stringify(newCategory.value),
    })
  } else {
    // Create new category
    response = await apiFetch('/expenses/expense-categories/', {
      method: 'POST',
      body: JSON.stringify(newCategory.value),
    })
  }
  
  if (response.ok) {
    createCategoryError.value = ''
    const updatedCategory = await response.json()
    
    if (editingId.value) {
      // Update existing category in list
      const index = categories.value.findIndex((c) => c.id === editingId.value)
      if (index !== -1) {
        categories.value[index] = updatedCategory
      }
      editingId.value = null
    } else {
      // Refresh categories list to get the new category
      await fetchCategories()
    }
    
    // Reset form
    newCategory.value = {
      id: 0,
      name: '',
      code: '',
      for_expense: true,
      is_active: true,
    }
  } else {
    const errorData = await response.json()
    createCategoryError.value = errorData?.detail || (editingId.value ? 'Failed to update category.' : 'Failed to create category.')
  }
}

function editCategory(category: Category) {
  editingId.value = category.id
  newCategory.value = {
    id: category.id,
    name: category.name,
    code: category.code,
    for_expense: category.for_expense,
    is_active: category.is_active,
  }
  // Scroll to form for better UX
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editingId.value = null
  newCategory.value = {
    id: 0,
    name: '',
    code: '',
    for_expense: true,
    is_active: true,
  }
}

async function deleteCategory(categoryId: number) {
  if (!confirm('Are you sure you want to delete this category?')) {
    return
  }
  
  deleteCategoryError.value = ''
  try {
    const response = await apiFetch(`/expenses/expense-categories/${categoryId}/`, {
      method: 'DELETE',
    })
    if (response.ok) {
      await fetchCategories()
    } else {
      const errorData = await response.json()
      deleteCategoryError.value = errorData?.detail || 'Failed to delete category.'
    }
  } catch (error) {
    console.error('Error deleting category:', error)
    deleteCategoryError.value = 'Failed to delete category.'
  }
}

onMounted(() => {
  fetchCategories().then(() => {})
})
</script>

<template>
  <h1 class="text-2xl font-bold mb-8">Categories</h1>
  <h2 class="text-xl font-bold mb-3">{{ editingId ? 'Edit Category' : 'Add Category' }}</h2>
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
    <div>
      <label for="is_active" class="flex items-center gap-2">
        <input
          type="checkbox"
          id="is_active"
          class="checkbox"
          v-model="newCategory.is_active"
        />
        Is Active
      </label>
    </div>
    <div class="col-span-full flex gap-2">
      <button type="submit" class="btn btn-primary">{{ editingId ? 'Update' : 'Add Category' }}</button>
      <button v-if="editingId" type="button" @click="cancelEdit" class="btn btn-secondary">Cancel</button>
    </div>
  </form>
  <div v-if="createCategoryError" class="text-red-50 my-4">{{ createCategoryError }}</div>
  <h2 class="text-xl font-bold mb-3 my-8">Categories List</h2>
  <div v-if="deleteCategoryError" class="text-red-50 my-4">{{ deleteCategoryError }}</div>
  <div class="overflow-x-auto">
    <table class="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Code</th>
          <th>For Expense</th>
          <th>Is Active</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="categories.length === 0">
          <td colspan="5" class="no-data">No categories found</td>
        </tr>
        <tr v-for="category in categories" :key="category.id">
          <td>{{ category.name }}</td>
          <td>{{ category.code }}</td>
          <td>{{ category.for_expense }}</td>
          <td>{{ category.is_active }}</td>
          <td>
            <div class="flex gap-2">
              <button
                @click="editCategory(category)"
                title="Edit"
                style="background: none; border: none; cursor: pointer"
              >
                <EditIcon />
              </button>
              <button
                @click="deleteCategory(category.id)"
                title="Delete"
                style="background: none; border: none; cursor: pointer"
              >
                <DeleteIcon />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <div v-if="fetchCategoriesError" class="text-red-50 my-4">{{ fetchCategoriesError }}</div>
</template>
