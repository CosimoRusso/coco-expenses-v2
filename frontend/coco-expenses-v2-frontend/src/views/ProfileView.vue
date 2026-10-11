<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiFetch from '@/utils/apiFetch'
import type { Currency } from '@/interfaces/Currency'
import type { Trip } from '@/interfaces/Trip'
import type { DefaultStatisticsMethod, UserSettings } from '@/interfaces/UserSettings'

const userStore = useUserStore()
const router = useRouter()

const userSettingsId = ref<number | null>(null)
const preferredCurrency = ref<number | null>(null)
const activeTrip = ref<number | null>(null)
const defaultStatisticsMethod = ref<DefaultStatisticsMethod>('HARDCODED_DATES')
const defaultStatisticsStartDate = ref<string>('')
const defaultStatisticsEndDate = ref<string>('')
const defaultStatisticsNDaysAgoFrom = ref<number | ''>('')
const defaultStatisticsNDaysAgoTo = ref<number | ''>('')
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
    const data: UserSettings = await response.json()
    userSettingsId.value = data.id
    preferredCurrency.value = data.preferred_currency
    activeTrip.value = data.active_trip
    defaultStatisticsMethod.value = data.default_statistics_method
    defaultStatisticsStartDate.value = data.default_statistics_start_date ?? ''
    defaultStatisticsEndDate.value = data.default_statistics_end_date ?? ''
    defaultStatisticsNDaysAgoFrom.value = data.default_statistics_n_days_ago_from ?? ''
    defaultStatisticsNDaysAgoTo.value = data.default_statistics_n_days_ago_to ?? ''
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

function numberOrNull(value: number | ''): number | null {
  return value === '' ? null : value
}

async function saveSettings() {
  const response = await apiFetch(`/expenses/user-settings/${userSettingsId.value}/`, {
    method: 'PATCH',
    body: JSON.stringify({
      preferred_currency: preferredCurrency.value,
      active_trip: activeTrip.value,
      default_statistics_method: defaultStatisticsMethod.value,
      default_statistics_start_date: defaultStatisticsStartDate.value || null,
      default_statistics_end_date: defaultStatisticsEndDate.value || null,
      default_statistics_n_days_ago_from: numberOrNull(defaultStatisticsNDaysAgoFrom.value),
      default_statistics_n_days_ago_to: numberOrNull(defaultStatisticsNDaysAgoTo.value),
    }),
  })
  if (response.ok) {
    saveSettingsStatus.value = 'Settings saved successfully'
  } else {
    const errorData = await response.json()
    saveSettingsStatus.value = errorData.non_field_errors?.[0] ?? 'Failed to save settings'
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

function logout() {
  userStore.logout()
  router.push('/login')
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
        <fieldset class="col-span-full grid grid-cols-1 md:grid-cols-2 gap-4">
          <legend class="mb-2">Default period of the statistics page</legend>
          <div class="col-span-full flex flex-wrap gap-x-6 gap-y-2">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                class="radio radio-primary"
                value="HARDCODED_DATES"
                v-model="defaultStatisticsMethod"
              />
              Fixed dates
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                class="radio radio-primary"
                value="DAYS_AGO"
                v-model="defaultStatisticsMethod"
              />
              Relative to today
            </label>
          </div>
          <template v-if="defaultStatisticsMethod === 'HARDCODED_DATES'">
            <div>
              <label for="defaultStatisticsStartDate">Statistics Start Date</label>
              <input
                type="date"
                id="defaultStatisticsStartDate"
                v-model="defaultStatisticsStartDate"
                class="input input-border w-full"
              />
              <p class="text-sm text-gray-500 mt-1">Leave empty to start 6 months ago</p>
            </div>
            <div>
              <label for="defaultStatisticsEndDate">Statistics End Date</label>
              <input
                type="date"
                id="defaultStatisticsEndDate"
                v-model="defaultStatisticsEndDate"
                class="input input-border w-full"
              />
              <p class="text-sm text-gray-500 mt-1">Leave empty to end today</p>
            </div>
          </template>
          <template v-else>
            <div>
              <label for="defaultStatisticsNDaysAgoFrom">From (days ago)</label>
              <input
                type="number"
                step="1"
                id="defaultStatisticsNDaysAgoFrom"
                v-model="defaultStatisticsNDaysAgoFrom"
                placeholder="180"
                class="input input-border w-full"
              />
              <p class="text-sm text-gray-500 mt-1">Leave empty to start 180 days ago</p>
            </div>
            <div>
              <label for="defaultStatisticsNDaysAgoTo">To (days ago)</label>
              <input
                type="number"
                step="1"
                id="defaultStatisticsNDaysAgoTo"
                v-model="defaultStatisticsNDaysAgoTo"
                placeholder="0"
                class="input input-border w-full"
              />
              <p class="text-sm text-gray-500 mt-1">
                Leave empty to end today. A negative number ends in the future: -30 is 30 days from
                now
              </p>
            </div>
          </template>
        </fieldset>
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
      <div class="border-t border-base-300 mt-6 pt-6">
        <button type="button" class="btn btn-outline btn-error" @click="logout">Logout</button>
      </div>
    </div>

    <div v-else class="bg-base-100 p-8 rounded-lg shadow text-center">
      <p>Please log in to view your profile.</p>
      <router-link to="/login" class="btn btn-primary mt-4">Go to Login</router-link>
    </div>
  </div>
</template>
