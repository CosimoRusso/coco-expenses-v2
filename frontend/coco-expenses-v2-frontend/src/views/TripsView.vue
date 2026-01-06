<script setup lang="ts">
import apiFetch from '@/utils/apiFetch'
import { onMounted, ref } from 'vue'
import EditIcon from '../../icons/EditIcon.vue'
import DeleteIcon from '../../icons/DeleteIcon.vue'

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
const deleteTripError = ref<string>('')
const editingId = ref<number | null>(null)

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
  createTripError.value = ''
  let response: Response
  
  if (editingId.value) {
    // Update existing trip
    response = await apiFetch(`/expenses/trips/${editingId.value}/`, {
      method: 'PUT',
      body: JSON.stringify(newTrip.value),
    })
  } else {
    // Create new trip
    response = await apiFetch('/expenses/trips/', {
      method: 'POST',
      body: JSON.stringify(newTrip.value),
    })
  }
  
  if (response.ok) {
    createTripError.value = ''
    const updatedTrip = await response.json()
    
    if (editingId.value) {
      // Update existing trip in list
      const index = trips.value.findIndex((t) => t.id === editingId.value)
      if (index !== -1) {
        trips.value[index] = updatedTrip
      }
      editingId.value = null
    } else {
      // Refresh trips list to get the new trip
      await fetchTrips()
    }
    
    // Reset form
    newTrip.value = {
      id: 0,
      name: '',
      code: '',
    }
  } else {
    const errorData = await response.json()
    createTripError.value = errorData?.detail || (editingId.value ? 'Failed to update trip.' : 'Failed to create trip.')
  }
}

function editTrip(trip: Trip) {
  editingId.value = trip.id
  newTrip.value = {
    id: trip.id,
    name: trip.name,
    code: trip.code,
  }
  // Scroll to form for better UX
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editingId.value = null
  newTrip.value = {
    id: 0,
    name: '',
    code: '',
  }
}

async function deleteTrip(tripId: number) {
  if (!confirm('Are you sure you want to delete this trip?')) {
    return
  }
  
  deleteTripError.value = ''
  try {
    const response = await apiFetch(`/expenses/trips/${tripId}/`, {
      method: 'DELETE',
    })
    if (response.ok) {
      await fetchTrips()
    } else {
      const errorData = await response.json()
      deleteTripError.value = errorData?.detail || 'Failed to delete trip.'
    }
  } catch (error) {
    console.error('Error deleting trip:', error)
    deleteTripError.value = 'Failed to delete trip.'
  }
}

onMounted(() => {
  fetchTrips().then(() => {})
})
</script>

<template>
  <h1 class="text-2xl font-bold mb-8">Trips</h1>
  <h2 class="text-xl font-bold mb-3">{{ editingId ? 'Edit Trip' : 'Add Trip' }}</h2>
  <form
    class="form grid grid-cols-1 md:grid-cols-2 gap-4"
    @submit.prevent="addTrip"
  >
    <div>
      <label for="name">Name</label>
      <input
        type="text"
        id="name"
        class="input input-border w-full"
        v-model="newTrip.name"
        required
      />
    </div>
    <div>
      <label for="code">Code</label>
      <input
        type="text"
        id="code"
        class="input input-border w-full"
        v-model="newTrip.code"
        required
      />
    </div>
    <div class="col-span-full flex gap-2">
      <button type="submit" class="btn btn-primary">{{ editingId ? 'Update' : 'Add Trip' }}</button>
      <button v-if="editingId" type="button" @click="cancelEdit" class="btn btn-secondary">Cancel</button>
    </div>
  </form>
  <div v-if="createTripError" class="text-red-50 my-4">{{ createTripError }}</div>
  <h2 class="text-xl font-bold mb-3 my-8">Trips List</h2>
  <div v-if="deleteTripError" class="text-red-50 my-4">{{ deleteTripError }}</div>
  <div class="overflow-x-auto">
    <table class="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Code</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="trips.length === 0">
          <td colspan="3" class="no-data">No trips found</td>
        </tr>
        <tr v-for="trip in trips" :key="trip.id">
          <td>{{ trip.name }}</td>
          <td>{{ trip.code }}</td>
          <td>
            <div class="flex gap-2">
              <button
                @click="editTrip(trip)"
                title="Edit"
                style="background: none; border: none; cursor: pointer"
              >
                <EditIcon />
              </button>
              <button
                @click="deleteTrip(trip.id)"
                title="Delete"
                style="background: none; border: none; cursor: pointer"
              >
                <DeleteIcon />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <div v-if="fetchTripsError" class="text-red-50 my-4">{{ fetchTripsError }}</div>
</template>
