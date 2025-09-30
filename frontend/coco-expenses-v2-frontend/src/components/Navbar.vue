<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { computed, ref, onMounted, onUnmounted } from 'vue'

const userStore = useUserStore()
const router = useRouter()

interface NavElement {
  text: string
  link?: string
  action?: () => void
}

const navElements = computed<NavElement[]>(() => {
  return [
    { text: 'Expenses', link: '/expenses' },
    { text: 'Categories', link: '/categories' },
    { text: 'Statistics', link: '/statistics' },
    ...(userStore.isLoggedIn
      ? [
          { text: 'Profile', link: '/profile' },
          { text: 'Logout', action: handleLogout },
        ]
      : [{ text: 'Login', link: '/login' }]),
  ]
})

const isMobileMenuOpen = ref(false)

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

// Responsive: update useMobileNavbar on resize
const useMobileNavbar = ref(window.innerWidth < 768)
function handleResize() {
  useMobileNavbar.value = window.innerWidth < 768
  if (!useMobileNavbar.value) isMobileMenuOpen.value = false
}
onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => window.removeEventListener('resize', handleResize))

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
    <template v-if="useMobileNavbar">
      <div class="mobile-menu">
        <button @click="toggleMobileMenu" class="menu-toggle">
          <span v-if="!isMobileMenuOpen">☰</span>
          <span v-else>✖</span>
        </button>
        <div v-if="isMobileMenuOpen" class="navbar-menu">
          <router-link
            :key="navElement.text"
            v-for="navElement in navElements"
            :to="navElement.link as string"
            class="navbar-item"
            >{{ navElement.text }}</router-link
          >
        </div>
      </div>
    </template>
    <template v-else>
      <div class="navbar-menu">
        <router-link
          :key="navElement.text"
          v-for="navElement in navElements"
          :to="navElement.link as string"
          class="navbar-item"
          >{{ navElement.text }}</router-link
        >
      </div>
    </template>
  </nav>
</template>

<style scoped>
:root {
  --color-primary: #4a90e2;
  --color-background-soft: #f5f5f5;
  --color-heading: #333;
  --color-text: black;
}

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

/* Mobile: vertical menu when open */
@media (max-width: 767px) {
  .navbar-menu {
    flex-direction: column;
    align-items: flex-end;
    background: white;
    position: absolute;
    top: 100%;
    right: 0;
    min-width: 180px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    border-radius: 0 0 8px 8px;
    padding: 1rem 1.5rem;
    z-index: 100;
  }
}

.navbar-item {
  color: black;
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

.router-link-active {
  color: var(--color-primary);
  font-weight: bold;
}

.mobile-menu {
  position: relative;
}

.menu-toggle {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  color: var(--color-text);
}

.menu-toggle:hover {
  color: var(--color-primary);
}

@media (min-width: 768px) {
  .mobile-menu {
    display: none;
  }
}
</style>
