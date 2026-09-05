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
const isEncrypted = ref<boolean>(false)
const passwordForEncryption = ref<string>('')
const encryptionActivationError = ref<string>('')
const isActivatingEncryption = ref<boolean>(false)

async function getUserSettings() {
  const response = await apiFetch('/expenses/user-settings/self/')
  if (response.ok) {
    const data = await response.json()
    userSettingsId.value = data.id
    preferredCurrency.value = data.preferred_currency
    activeTrip.value = data.active_trip
    isEncrypted.value = data.is_encrypted
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

async function activateEncryption() {
  encryptionActivationError.value = ''
  if (isEncrypted.value) {
    encryptionActivationError.value = 'You are already encrypted'
    return
  }
  if (!passwordForEncryption.value) {
    encryptionActivationError.value = 'Insert your password first!'
    return
  }
  isActivatingEncryption.value = true
  const response = await apiFetch('/expenses/user-settings/activate_encryption/', {
    method: 'POST',
    body: JSON.stringify({
      password: passwordForEncryption.value,
    }),
  })
  isActivatingEncryption.value = false
  if (!response.ok) {
    if (response.status === 400) {
      const error = await response.json()
      if ('password' in error) {
        encryptionActivationError.value = error.password[0]
      }
    } else if (response.status === 500) {
      encryptionActivationError.value = "Errore imprevisto nell'attivazione dell'encryption"
    }
    return
  }
  isEncrypted.value = true
}

onMounted(() => {
  fetchData().then(() => {})
})
</script>

<template>
  <div class="max-w-3xl mx-auto p-5">
    <h1 class="text-2xl font-bold mb-6">User Profile</h1>
    <div v-if="userStore.isLoggedIn" class="bg-base-100 p-6 rounded-lg shadow mb-6">
      <p class="mb-4">Welcome to your profile page!</p>
      <p v-if="userStore.email" class="mb-4">Email: {{ userStore.email }}</p>

      <form
        class="form grid grid-cols-1 md:grid-cols-2 gap-4 bg-base-100 p-6 rounded-lg shadow mb-6"
        @submit.prevent="saveSettings"
      >
        <p class="mb-4 col-span-full">Here are your profile settings:</p>
        <div>
          <label for="preferredCurrency">Preferred Currency</label>
          <select
            id="preferredCurrency"
            v-model="preferredCurrency"
            class="select input input-border w-full"
          >
            <option :value="null">Select a currency</option>
            <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
              {{ currency.display_name }}
            </option>
          </select>
        </div>
        <div>
          <label for="activeTrip">Active Trip</label>
          <select id="activeTrip" v-model="activeTrip" class="select input input-border w-full">
            <option :value="null">Select a trip</option>
            <option v-for="trip in trips" :key="trip.id" :value="trip.id">
              {{ trip.name }}
            </option>
          </select>
        </div>
        <div class="col-span-full">
          <button type="submit" class="btn btn-primary">Save</button>
        </div>
        <div class="col-span-full">
          <p
            v-if="saveSettingsStatus"
            :class="saveSettingsStatus.includes('successfully') ? 'text-success' : 'text-error'"
          >
            {{ saveSettingsStatus }}
          </p>
        </div>
      </form>
      <div
        v-if="isEncrypted === false"
        class="grid cols-1 md-grid-cols-2 w-full bg-base-100 p-6 rounded-lg shadow mb-6"
      >
        <div class="mb-3">
          <label for="password_for_encryption">Insert password to activate encryption:</label>
          <input
            v-model="passwordForEncryption"
            id="password_for_encryption"
            type="password"
            class="input w-full"
          />
        </div>
        <button
          :disabled="isActivatingEncryption"
          @click="activateEncryption"
          type="submit"
          class="btn btn-primary mb-3"
        >
          Activate encryption
        </button>

        <p class="text-red-500" v-if="encryptionActivationError">{{ encryptionActivationError }}</p>
      </div>
      <p v-else>You are encrypted, disabling encryption is not implemented yet :)</p>
    </div>

    <div v-else class="bg-base-100 p-8 rounded-lg shadow text-center">
      <p>Please log in to view your profile.</p>
      <router-link to="/login" class="btn btn-primary mt-4">Go to Login</router-link>
    </div>
  </div>
</template>
