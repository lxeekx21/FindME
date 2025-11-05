<template>
  <div class="p-6 max-w-3xl mx-auto">
    <!-- Alert details -->
    <div class="bg-white rounded-lg shadow p-4">
      <img
        :src="alert.image"
        :alt="alert.name"
        class="w-full h-56 object-cover rounded"
      />
      <h1 class="mt-4 text-2xl font-bold">{{ alert.name }}</h1>
      <p class="text-gray-600 mt-1">Age: {{ alert.age }}</p>
      <p class="text-gray-600">Province: {{ alert.province }}</p>
      <p class="text-gray-600 mt-2">{{ alert.description }}</p>
      <p class="text-sm text-gray-400 mt-2">Last seen: {{ alert.last_seen }}</p>
    </div>

    <!-- Comments section -->
    <div class="mt-6">
      <CommentsSection :alertId="alert.id" />
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { ref } from 'vue'
import CommentsSection from '~/components/CommentsSection.vue'

// 🔹 mock data to be replaced by backend
const allAlerts = [
  {
    id: 1,
    name: 'Lerato Mokoena',
    age: 15,
    province: 'Gauteng',
    last_seen: '2025-10-15',
    image: '/default.jpg',
    description: 'Last seen near Park Station.',
  },
  {
    id: 2,
    name: 'Thabo Nkosi',
    age: 17,
    province: 'KwaZulu-Natal',
    last_seen: '2025-10-12',
    image: '/default.jpg',
    description: 'Missing from Umlazi area.',
  },
  {
    id: 3,
    name: 'Zanele Dlamini',
    age: 21,
    province: 'Western Cape',
    last_seen: '2025-10-18',
    image: '/default.jpg',
    description: 'Reported missing in Bellville.',
  },
]

// get ID from route (like /alerts/2)
const route = useRoute()
const alert = ref(allAlerts.find(a => a.id === Number(route.params.id)))
</script>
