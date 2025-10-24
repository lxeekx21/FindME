<script setup lang="ts">
defineProps<{
  icon: string
  label: string
  to: string
}>()
</script>

<template>
  <NuxtLink :to="to" class="group">
    <div
      class="flex h-24 w-24 transform flex-col items-center justify-center bg-white/10 shadow-lg shadow-indigo-400/30 backdrop-blur-md transition duration-300 group-hover:shadow-2xl group-hover:shadow-indigo-400/70">
      <UIcon :name="icon" class="h-8 w-8 text-white drop-shadow-md" />
      <span class="mt-2 text-xs font-medium text-white drop-shadow">
        {{ label }}
      </span>
    </div>
  </NuxtLink>
</template>
