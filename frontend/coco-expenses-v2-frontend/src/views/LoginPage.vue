<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const router = useRouter()

async function handleLogin() {
  // Reset error message
  errorMessage.value = ''

  // Basic validation
  if (!email.value || !password.value) {
    errorMessage.value = 'Please enter both email and password'
    return
  }

  const body = JSON.stringify({ email: email.value, password: password.value })

  const response = await fetch('/api/expenses/users/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  })
  if (response.ok) {
    await router.push('/')
  } else if (response.status === 403) {
    const msg = await response.json()
    errorMessage.value = msg.detail
  } else {
    console.error(response)
    errorMessage.value = 'Unexpected error'
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-form">
      <h1>Login</h1>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <div class="form-group">
        <label for="email">email</label>
        <input
          id="email"
          v-model="email"
          type="text"
          placeholder="Enter your email"
          autocomplete="email"
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="Enter your password"
          autocomplete="current-password"
        />
      </div>

      <button @click="handleLogin" class="login-button">Login</button>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.login-form {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
  background-color: var(--color-background-soft);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: var(--color-heading);
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: var(--color-text);
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background-color: var(--color-background);
  color: var(--color-text);
  font-size: 1rem;
  transition: border-color 0.3s;
}

input:focus {
  outline: none;
  border-color: var(--color-border-hover);
  box-shadow: 0 0 0 2px hsla(160, 100%, 37%, 0.2);
}

.login-button {
  width: 100%;
  padding: 0.75rem;
  margin-top: 1rem;
  background-color: hsla(160, 100%, 37%, 1);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.login-button:hover {
  background-color: hsla(160, 100%, 37%, 0.8);
}

.error-message {
  background-color: rgba(255, 0, 0, 0.1);
  color: #d32f2f;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  text-align: center;
}
</style>
