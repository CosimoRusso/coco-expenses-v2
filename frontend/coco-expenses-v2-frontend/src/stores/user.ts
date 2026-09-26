import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import apiFetch from '@/utils/apiFetch.ts'

export const useUserStore = defineStore('user', () => {
  const isLoggedIn = ref(false)
  const id = ref<number | null>(null)
  const email = ref('')
  const firstName = ref('')
  const lastName = ref('')

  function initUser(userData: { id: number; email: string; firstName: string; lastName: string }) {
    id.value = userData.id
    email.value = userData.email
    firstName.value = userData.firstName
    lastName.value = userData.lastName
    isLoggedIn.value = true
  }

  async function checkAuthStatus() {
    const response = await apiFetch('expenses/users/self/')
    if (response.ok) {
      const userData = await response.json()
      initUser({
        id: userData.id,
        email: userData.email,
        firstName: userData.first_name,
        lastName: userData.last_name,
      })
      isLoggedIn.value = true
    } else {
      isLoggedIn.value = false
    }
  }

  async function logout() {
    await apiFetch('expenses/users/logout/', {
      method: 'POST',
    })
    localStorage.removeItem('token')
    id.value = null
    email.value = ''
    firstName.value = ''
    lastName.value = ''
    isLoggedIn.value = false
  }

  const fullName = computed(() => `${firstName.value} ${lastName.value}`)

  // Initialize auth status
  checkAuthStatus().catch(() => {})

  return {
    isLoggedIn,
    id,
    logout,
    checkAuthStatus,
    initUser,
    email,
    fullName,
  }
})
