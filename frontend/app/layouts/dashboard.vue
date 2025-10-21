<script setup lang="ts">
const route = useRoute()
const title = computed(() => {
  const path = route.path.split('/').pop() || 'dashboard'
  return path
    .split('-')
    .map(s => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
})

const sidebarOpen = ref(false)
const collapsed = ref(false)

// Ensure the browser tab has a proper title and a consistent suffix on all dashboard pages
useHead(() => ({
  title: title.value,
  titleTemplate: '%s · FindSouth',
}))
</script>

<template>
  <div class="h-screen overflow-hidden bg-fs-100 text-fs-800 flex">
    <!-- Sidebar (handles both mobile drawer and desktop fixed) -->
    <DashboardSidebar :open="sidebarOpen" :collapsed="collapsed" @close="sidebarOpen = false" />

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-h-0">
      <header class="bg-white border-b border-primary-800 px-4 h-14 flex items-center gap-3 shrink-0">
        <button
          type="button"
          class="md:hidden inline-flex items-center justify-center rounded-md p-2 text-fs-600 hover:bg-fs-100 focus:outline-none focus:ring-2 focus:ring-fs-300"
          aria-label="Open sidebar"
          @click="sidebarOpen = true"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5" />
          </svg>
        </button>
        <!-- Desktop collapse toggle -->
        <button
          type="button"
          class="hidden md:inline-flex items-center justify-center rounded-md p-2 text-fs-600 hover:bg-fs-100 focus:outline-none focus:ring-2 focus:ring-fs-300"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="collapsed = !collapsed"
          :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        >
          <svg v-if="!collapsed" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 12h-15m6 6-6-6 6-6" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12h15m-6-6 6 6-6 6" />
          </svg>
        </button>
        <h1 class="text-xl font-semibold text-fs-700">{{ title }}</h1>
      </header>
      <main class="p-4 bg-white flex-1 min-h-0 overflow-y-auto">
        <slot />
      </main>
    </div>
  </div>
</template>
