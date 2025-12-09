<script setup lang="ts">
import apiFetch from '@/utils/apiFetch'
import { onMounted, ref } from 'vue'

interface Trip {
  id: number
  name: string
  code: string
}

const newTrip = ref<Trip>({
  id: 0,
  name: '',
  code: '',
})

const createTripError = ref<string>('')
const trips = ref<Trip[]>([])
const fetchTripsError = ref<string>('')

async function fetchTrips() {
  fetchTripsError.value = ''
  const response = await apiFetch('/expenses/trips/')
  if (response.ok) {
    trips.value = await response.json()
  } else {
    const errorData = await response.json()
    fetchTripsError.value = errorData?.detail || 'Failed to fetch trips.'
  }
}

async function addTrip() {
  const response = await apiFetch('/expenses/trips/', {
    method: 'POST',
    body: JSON.stringify(newTrip.value),
  })
  if (response.ok) {
    createTripError.value = ''
    newTrip.value = {
      id: 0,
      name: '',
      code: '',
    }
    await fetchTrips()
  } else {
    const errorData = await response.json()
    createTripError.value = errorData?.detail || 'Failed to create trip.'
  }
}

onMounted(() => {
  fetchTrips().then(() => {})
})
</script>

<template>
  <h1>Trips</h1>
  <h2>Add Trip</h2>
  <form @submit.prevent="addTrip">
    <div>
      <label for="name">Name</label>
      <input type="text" id="name" v-model="newTrip.name" required />
    </div>
    <div>
      <label for="code">Code</label>
      <input type="text" id="code" v-model="newTrip.code" required />
    </div>
    <button type="submit">Add Trip</button>
  </form>
  <p v-if="createTripError" class="error">{{ createTripError }}</p>
  <h2>Trips List</h2>
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Code</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="trip in trips" :key="trip.id">
        <td>{{ trip.name }}</td>
        <td>{{ trip.code }}</td>
      </tr>
    </tbody>
  </table>
  <p v-if="fetchTripsError" class="error">{{ fetchTripsError }}</p>
</template>

<style scoped>
.error {
  color: red;
  font-weight: bold;
  margin-bottom: 10px;
}
</style>
