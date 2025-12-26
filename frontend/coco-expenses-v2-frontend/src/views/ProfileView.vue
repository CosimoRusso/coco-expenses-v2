<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { ref, onMounted } from 'vue'
import apiFetch from '@/utils/apiFetch'
import type { Currency } from '@/interfaces/Currency'
import type { Trip } from '@/interfaces/Trip'

const userStore = useUserStore()

const userSettingsId = ref<number | null>(null)
const preferredCurrency = ref<number | null>(null)
const activeTrip = ref<number | null>(null)
const currencies = ref<Currency[]>([])
const trips = ref<Trip[]>([])
const saveSettingsStatus = ref<string>('')

async function getUserSettings() {
  const response = await apiFetch('/expenses/user-settings/self/')
  if (response.ok) {
    const data = await response.json()
    userSettingsId.value = data.id
    preferredCurrency.value = data.preferred_currency
    activeTrip.value = data.active_trip
  }
}

async function getCurrencies() {
  const response = await apiFetch('/expenses/currencies/')
  if (response.ok) {
    const data = await response.json()
    currencies.value = data
  }
}

async function getTrips() {
  const response = await apiFetch('/expenses/trips/')
  if (response.ok) {
    const data = await response.json()
    trips.value = data
  }
}

async function fetchData() {
  await Promise.all([getUserSettings(), getCurrencies(), getTrips()])
}

async function saveSettings() {
  const response = await apiFetch(`/expenses/user-settings/${userSettingsId.value}/`, {
    method: 'PATCH',
    body: JSON.stringify({
      preferred_currency: preferredCurrency.value,
      active_trip: activeTrip.value,
    }),
  })
  if (response.ok) {
    saveSettingsStatus.value = 'Settings saved successfully'
  } else {
    saveSettingsStatus.value = 'Failed to save settings'
    const errorData = await response.json()
    console.log(errorData)
  }
}

onMounted(() => {
  fetchData().then(() => {})
})
</script>

<template>
  <div class="profile">
    <h1>User Profile</h1>
    <div v-if="userStore.isLoggedIn" class="profile-content">
      <p>Welcome to your profile page!</p>
      <p v-if="userStore.email">Email: {{ userStore.email }}</p>
      <p>Here are your profile settings:</p>
      <form @submit.prevent="saveSettings">
        <div>
          <label for="preferredCurrency">Preferred Currency</label>
          <select id="preferredCurrency" v-model="preferredCurrency">
            <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
              {{ currency.display_name }}
            </option>
          </select>
        </div>
        <div>
          <label for="activeTrip">Active Trip</label>
          <select id="activeTrip" v-model="activeTrip">
            <option v-for="trip in trips" :key="trip.id" :value="trip.id">{{ trip.name }}</option>
          </select>
        </div>
        <button type="submit">Save</button>
        <p v-if="saveSettingsStatus">{{ saveSettingsStatus }}</p>
      </form>
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
