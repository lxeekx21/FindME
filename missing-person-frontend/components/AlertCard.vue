<template>
  <div class="bg-white rounded-lg shadow p-4 w-full max-w-md">
    <img :src="alert.image" :alt="alert.name" class="w-full h-40 object-cover rounded" />
    <h3 class="mt-3 font-bold text-lg">{{ alert.name }} <span class="text-sm text-gray-500">({{ alert.age }})</span></h3>
    <p class="text-sm text-gray-600 mt-1">{{ alert.description }}</p>
    <div class="mt-3 flex justify-between items-center">
      <span class="text-xs text-gray-500">{{ alert.province }} • {{ alert.last_seen }}</span>
      <NuxtLink :to="`/alerts/${alert.id}`" class="text-blue-600 text-sm">View</NuxtLink>
    </div>
  </div>
</template>

<script setup>
defineProps({ alert: Object })
</script>
