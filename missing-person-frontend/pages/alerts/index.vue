<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Active Missing Person Alerts</h1>

    <ProvinceFilter @change="filterByProvince" />

    <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <AlertCard
        v-for="a in filteredAlerts"
        :key="a.id"
        :alert="a"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ProvinceFilter from '~/components/ProvinceFilter.vue'
import AlertCard from '~/components/AlertCard.vue'

//mock data to be replaced with backend
const alerts = ref([
  { id: 1, name: 'Lerato Mokoena', age: 15, province: 'Gauteng', last_seen: '2025-10-15', image: '/default.jpg', description: 'Last seen near Park Station.' },
  { id: 2, name: 'Thabo Nkosi', age: 17, province: 'KwaZulu-Natal', last_seen: '2025-10-12', image: '/default.jpg', description: 'Missing from Umlazi area.' },
  { id: 3, name: 'Zanele Dlamini', age: 21, province: 'Western Cape', last_seen: '2025-10-18', image: '/default.jpg', description: 'Reported missing in Bellville.' }
])

const selectedProvince = ref('Gauteng')
const filteredAlerts = computed(() =>
  alerts.value.filter(a => a.province === selectedProvince.value)
)

function filterByProvince(province) {
  selectedProvince.value = province
}
</script>
