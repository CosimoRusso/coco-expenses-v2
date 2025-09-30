<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<template>
  <div class="profile">
    <h1>User Profile</h1>
    <div v-if="userStore.isLoggedIn" class="profile-content">
      <p>Welcome to your profile page!</p>
      <p v-if="userStore.email">Email: {{ userStore.email }}</p>
      <p>Profile settings and user information will be added in future updates.</p>
    </div>
    <div v-else class="login-required">
      <p>Please log in to view your profile.</p>
      <router-link to="/login" class="login-link">Go to Login</router-link>
    </div>
  </div>
</template>

<style scoped>
.profile {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  margin-bottom: 1.5rem;
}

.profile-content {
  background-color: var(--color-background-soft);
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.login-required {
  text-align: center;
  padding: 2rem;
  background-color: var(--color-background-soft);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.login-link {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: var(--color-primary);
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 500;
  transition: background-color 0.3s;
}

.login-link:hover {
  background-color: var(--color-primary-dark, hsl(160, 100%, 30%));
}
</style>
