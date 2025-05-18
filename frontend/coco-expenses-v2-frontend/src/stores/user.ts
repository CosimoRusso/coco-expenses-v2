import { defineStore } from 'pinia'
import { ref } from 'vue'
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
    const response = await apiFetch('expenses/users/self')
    if (response.ok) {
      const userData = await response.json()
      initUser(userData)
      isLoggedIn.value = true
    } else {
      isLoggedIn.value = false
    }
  }

  function logout() {
    localStorage.removeItem('token')
    email.value = ''
    firstName.value = ''
    lastName.value = ''
    isLoggedIn.value = false
  }

  // Initialize auth status
  checkAuthStatus().catch(() => {})

  return {
    isLoggedIn,
    logout,
    checkAuthStatus,
    initUser,
  }
})
