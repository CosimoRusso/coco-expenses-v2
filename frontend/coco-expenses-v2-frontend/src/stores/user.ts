import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import apiFetch from '@/utils/apiFetch.ts'

export const useUserStore = defineStore('user', () => {
  const isLoggedIn = ref(false)
  const email = ref('')
  const firstName = ref('')
  const lastName = ref('')

  function initUser(userData: { email: string; firstName: string; lastName: string }) {
    email.value = userData.email
    firstName.value = userData.firstName
    lastName.value = userData.lastName
    isLoggedIn.value = true
  }

  async function checkAuthStatus() {
    const response = await apiFetch('expenses/users/self/')
    if (response.ok) {
      const userData = await response.json()
      initUser(userData)
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
    logout,
    checkAuthStatus,
    initUser,
    email,
    fullName,
  }
})
