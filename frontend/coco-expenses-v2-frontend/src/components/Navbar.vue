<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

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
    <div class="navbar-menu">
      <router-link to="/expenses" class="navbar-item">Expenses</router-link>
      <router-link to="/statistics" class="navbar-item">Statistics</router-link>
      <template v-if="userStore.isLoggedIn">
        <router-link to="/profile" class="navbar-item">Profile</router-link>
        <button @click="handleLogout" class="navbar-item logout-button">Logout</button>
      </template>
      <router-link v-else to="/login" class="navbar-item">Login</router-link>
    </div>
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
