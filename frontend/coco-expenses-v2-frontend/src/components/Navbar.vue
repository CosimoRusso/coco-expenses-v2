<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { computed } from 'vue'

const userStore = useUserStore()
const router = useRouter()

interface NavElement {
  text: string
  link: string
}

const navElements: NavElement[] = [
  { text: 'Expenses', link: '/expenses' },
  { text: 'Categories', link: '/categories' },
  { text: 'Statistics', link: '/statistics' },
  ...(userStore.isLoggedIn
    ? [
        { text: 'Profile', link: '/profile' },
        { text: 'Logout', link: '/logout' },
      ]
    : [{ text: 'Login', link: '/login' }]),
]

const useMobileNavbar = computed(() => {
  return window.innerWidth < 768
})

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <nav class="navbar">
    <div class="navbar-brand">
      <router-link to="/" class="logo">CocoExpenses</router-link>
    </div>
    <template v-if="useMobileNavbar"></template>
    <template v-else>
      <div class="navbar-menu">
        <router-link
          :key="navElement.text"
          v-for="navElement in navElements"
          :to="navElement.link"
          class="navbar-item"
          >{{ navElement.text }}</router-link
        >
      </div>
    </template>
  </nav>
</template>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: var(--color-background-soft);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
  font-size: 1.5rem;
  font-weight: bold;
}

.logo {
  color: var(--color-heading);
  text-decoration: none;
}

.navbar-menu {
  display: flex;
  gap: 1.5rem;
}

.navbar-item {
  color: var(--color-text);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
}

.navbar-item:hover {
  color: var(--color-primary);
}

.logout-button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  padding: 0;
  color: var(--color-text);
}

.logout-button:hover {
  color: var(--color-primary);
}

.router-link-active {
  color: var(--color-primary);
  font-weight: bold;
}
</style>
