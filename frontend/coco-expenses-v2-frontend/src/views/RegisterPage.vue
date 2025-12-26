<script setup lang="ts">
import { ref } from 'vue'
import apiFetch from '@/utils/apiFetch.ts'

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const firstName = ref('')
const lastName = ref('')
const errorMessage = ref('')
const registrationSuccess = ref(false)

async function handleRegister() {
  // Reset messages
  errorMessage.value = ''
  registrationSuccess.value = false

  // Basic validation
  if (!email.value || !password.value || !firstName.value || !lastName.value) {
    errorMessage.value = 'Please fill in all fields'
    return
  }

  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match'
    return
  }

  if (password.value.length < 6) {
    errorMessage.value = 'Password must be at least 6 characters long'
    return
  }

  const body = JSON.stringify({
    email: email.value,
    password: password.value,
    first_name: firstName.value,
    last_name: lastName.value,
  })

  try {
    const response = await apiFetch('expenses/users/register/', {
      method: 'POST',
      body,
    })

    if (response.ok) {
      registrationSuccess.value = true
      // Clear form
      email.value = ''
      password.value = ''
      confirmPassword.value = ''
      firstName.value = ''
      lastName.value = ''
    } else {
      const errorData = await response.json()
      if (response.status >= 400 && response.status < 500) {
        // Handle validation errors
        if (errorData.detail) {
          errorMessage.value = errorData.detail
        } else if (errorData.email) {
          errorMessage.value = 'Email: ' + errorData.email[0]
        } else if (errorData.password) {
          errorMessage.value = 'Password: ' + errorData.password[0]
        } else {
          errorMessage.value = 'Please check your input and try again'
        }
      } else {
        errorMessage.value = 'Registration failed. Please try again.'
      }
    }
  } catch (error) {
    console.error('Registration error:', error)
    errorMessage.value = 'An unexpected error occurred. Please try again.'
  }
}
</script>

<template>
  <div class="register-container">
    <div v-if="registrationSuccess" class="success-message">
      Registration successful! You can now <router-link to="/login">login</router-link>.
    </div>
    <div v-else class="register-form">
      <h1>Register</h1>
      <div class="form-group">
        <label for="firstName">First Name</label>
        <input
          id="firstName"
          v-model="firstName"
          type="text"
          placeholder="Enter your first name"
          autocomplete="given-name"
        />
      </div>

      <div class="form-group">
        <label for="lastName">Last Name</label>
        <input
          id="lastName"
          v-model="lastName"
          type="text"
          placeholder="Enter your last name"
          autocomplete="family-name"
        />
      </div>

      <div class="form-group">
        <label for="email">Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
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
          autocomplete="new-password"
        />
      </div>

      <div class="form-group">
        <label for="confirmPassword">Confirm Password</label>
        <input
          id="confirmPassword"
          v-model="confirmPassword"
          type="password"
          placeholder="Confirm your password"
          autocomplete="new-password"
        />
      </div>

      <button @click="handleRegister" class="register-button">Register</button>
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <div class="login-link">
        <p>Already have an account? <router-link to="/login">Login here</router-link></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.register-form {
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

.register-button {
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

.register-button:hover {
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

.success-message {
  background-color: rgba(0, 255, 0, 0.1);
  color: #2e7d32;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  text-align: center;
}

.login-link {
  text-align: center;
  margin-top: 1rem;
}

.login-link p {
  color: var(--color-text);
  margin: 0;
}

.login-link a {
  color: hsla(160, 100%, 37%, 1);
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
