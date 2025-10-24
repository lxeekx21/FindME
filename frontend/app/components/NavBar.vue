<script setup lang="ts">
const { isAuthenticated, user, initializeAuth } = useAuth()
const router = useRouter()
const { apiBase } = useRuntimeConfig().public

await initializeAuth()

const menuOpen = ref(false)

const goDashboard = () => router.push('/dashboard/my-profile')
const goLogin = () => router.push('/login')
const goRegister = () => router.push('/register')
const goHome = () => router.push('/')

function toAbsoluteUrl(url?: string | null): string | null {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/')) return `${apiBase?.replace(/\/$/, '')}${url}`
  return url
}

const avatarUrl = computed(() => {
  const raw = user.value?.profile_image_url
  const abs = toAbsoluteUrl(raw)
  if (abs) return abs
  const seed = `${user.value?.first_name || 'F'}${user.value?.last_name || 'S'}`
  return `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(seed)}`
})

</script>

<template>
  <nav class="sticky top-0 z-40 w-full border-b border-primary-800 bg-primary-700">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-16 items-center justify-between">
        <!-- Left: Logo -->
        <div class="flex items-center gap-3 cursor-pointer" @click="goHome">
          <img src="/images/logo-white.png" alt="FindSouth" class="h-8 w-auto" onerror="this.style.display='none'" />
        </div>

        <!-- Right: auth -->
        <div class="hidden md:flex items-center gap-3">
          <template v-if="isAuthenticated">
            <button class="hidden sm:inline-flex items-center gap-2 rounded-md border text-white cursor-pointer border-white px-3 py-1.5 text-sm hover:bg-neutral-50" @click="goDashboard">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5 text-white">
                <path d="M3 12l9-9 9 9v8.25A1.75 1.75 0 0 1 19.25 21h-3.5A1.75 1.75 0 0 1 14 19.25v-3.5A1.75 1.75 0 0 0 12.25 14h-0.5A1.75 1.75 0 0 0 10 15.75v3.5A1.75 1.75 0 0 1 8.25 21h-3.5A1.75 1.75 0 0 1 3 19.25V12z" />
              </svg>
              Dashboard
            </button>
            <NuxtLink to="/dashboard/my-profile">
              <img :src="avatarUrl" alt="avatar" class="h-9 w-9 rounded-full border border-neutral-200" />
            </NuxtLink>
          </template>
          <template v-else>
            <button class="rounded-md border border-white/70 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-600/80 cursor-pointer" @click="goLogin">Login</button>
            <button class="rounded-md bg-white px-3 py-1.5 text-sm font-medium text-primary-700 cursor-pointer" @click="goRegister">Create account</button>
          </template>
        </div>

        <!-- Mobile -->
        <div class="md:hidden">
          <button class="inline-flex items-center justify-center rounded-md p-2 text-neutral-700 hover:bg-neutral-100" @click="menuOpen = !menuOpen" aria-label="Toggle menu">
            <svg v-if="!menuOpen" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <div v-if="menuOpen" class="md:hidden border-t border-neutral-200 bg-white">
      <div class="space-y-2 px-4 py-3">
        <template v-if="isAuthenticated">
          <button class="w-full text-left rounded-md border border-neutral-200 px-3 py-2 text-sm" @click="goDashboard">Dashboard</button>
        </template>
        <template v-else>
          <button class="w-full text-left rounded-md px-3 py-2 text-sm" @click="goLogin">Login</button>
          <button class="w-full text-left rounded-md bg-neutral-900 px-3 py-2 text-sm font-medium text-white" @click="goRegister">Create account</button>
        </template>
      </div>
    </div>
  </nav>
</template>
