<script setup lang="ts">
const route = useRoute()
const { user, logout } = useAuth()

const props = defineProps<{ open?: boolean; collapsed?: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const role = computed(() => {
  const names = (user.value?.roles || []).map(r => r.name?.toLowerCase())
  if (names.includes('admin') || names.includes('admission')) return 'admin'
  return 'user'
})

// Simple inline SVG icons (Heroicons outline style) using currentColor
const icons: Record<string, string> = {
  comments: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3h6.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>`,
  userComments: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3h6.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>`,
  submissions: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 8.25h18M3 15.75h18M9.75 3v18m4.5-18v18"/></svg>`,
  users: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9 9 0 1 0-6 0M12 14.25a3.75 3.75 0 1 0 0-7.5 3.75 3.75 0 0 0 0 7.5Z"/></svg>`,
  mySubmissions: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v2.25A2.25 2.25 0 0 1 17.25 18.75H6.75A2.25 2.25 0 0 1 4.5 16.5v-9A2.25 2.25 0 0 1 6.75 5.25H12l3 3h2.25A2.25 2.25 0 0 1 19.5 10.5v.75M9 13.5h6M9 10.5h3"/></svg>`,
  newSubmission: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m6-6H6"/></svg>`,
  profile: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6.75a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.5 19.5a7.5 7.5 0 0 1 15 0"/></svg>`,
  logout: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3H6.75A2.25 2.25 0 0 0 4.5 5.25v13.5A2.25 2.25 0 0 0 6.75 21h6.75a2.25 2.25 0 0 0 2.25-2.25V15M12 9l3-3m0 0 3 3m-3-3v12"/></svg>`,
  analytics: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 3v18h18M7.5 15.75V12m4.5 3.75V9m4.5 6.75V6"/></svg>`,
  heatmap: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-5 w-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7.5a4.5 4.5 0 0 1 9 0V9a3 3 0 0 0 3 3h1.5a4.5 4.5 0 1 1 0 9H8.25A5.25 5.25 0 0 1 3 15.75V7.5z"/></svg>`,
}

const menuItems = computed(() => {
  if (role.value === 'admin') {
    return [
      { label: 'Submissions', to: '/dashboard/submissions', icon: 'submissions' },
      { label: 'User Comments', to: '/dashboard/user-comments', icon: 'userComments' },
      { label: 'Analytics', to: '/dashboard/analytics', icon: 'analytics' },
      { label: 'Heat Map', to: '/dashboard/heat-map', icon: 'heatmap' },
      { label: 'User Accounts', to: '/dashboard/user-accounts', icon: 'users' },
    ]
  }
  return [
    { label: 'My Submissions', to: '/dashboard/my-submissions', icon: 'mySubmissions' },
    { label: 'My Comments', to: '/dashboard/my-comments', icon: 'comments' },
    { label: 'New Submission', to: '/dashboard/new-submission', icon: 'newSubmission' },
  ]
})

const bottomItems = [
  { label: 'My Profile', to: '/dashboard/my-profile', icon: 'profile' },
]

const isActive = (to: string) => route.path === to

const linkBase =
  'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors'

const handleLogout = async () => {
  await logout()
  await navigateTo('/')
}
</script>

<template>
  <!-- Mobile overlay -->
  <transition name="fade">
    <div
      v-if="props.open"
      class="fixed inset-0 z-40 bg-black/50 backdrop-blur-[1px] md:hidden"
      @click.self="emit('close')"
    />
  </transition>

  <!-- Mobile drawer -->
  <div
    class="fixed inset-y-0 left-0 z-50 w-64 transform bg-primary-900 border-r border-primary-800 text-primary-50 transition-transform duration-200 ease-in-out md:hidden"
    :class="props.open ? 'translate-x-0' : '-translate-x-full'"
    role="dialog"
    aria-modal="true"
  >
    <div class="flex items-center justify-between p-4 border-b border-primary-800">
      <NuxtLink to="/" class="inline-flex items-center gap-2">
        <img src="/images/logo-white.png" alt="FindSouth" class="h-6 w-auto" />
      </NuxtLink>
      <button
        type="button"
        class="inline-flex items-center justify-center rounded-md p-2 text-primary-100 hover:bg-primary-700"
        aria-label="Close sidebar"
        @click="emit('close')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-6 w-6">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <nav class="flex-1 px-2 py-2 pt-4 space-y-1 overflow-y-auto">
      <NuxtLink
        v-for="item in menuItems"
        :key="item.to"
        :to="item.to"
        :class="[linkBase, isActive(item.to) ? 'bg-primary-700 text-white font-semibold border-l-2 border-primary-400' : 'text-primary-100 hover:bg-primary-700']"
        @click="emit('close')"
        :title="item.label"
      >
        <span class="inline-flex items-center" v-html="icons[item.icon]"></span>
        <span>{{ item.label }}</span>
      </NuxtLink>
    </nav>

    <div class="border-t border-primary-700 p-2 space-y-1">
      <NuxtLink
        v-for="item in bottomItems"
        :key="item.to"
        :to="item.to"
        :class="[linkBase, isActive(item.to) ? 'bg-primary-700 text-white font-semibold border-l-2 border-primary-400' : 'text-primary-100 hover:bg-primary-700']"
        @click="emit('close')"
        :title="item.label"
      >
        <span v-if="item.to === '/dashboard/my-profile' && user?.profile_image_url" class="inline-flex items-center">
          <img :src="user?.profile_image_url" alt="Profile" class="h-5 w-5 rounded-full object-cover border border-primary-400" />
        </span>
        <span v-else class="inline-flex items-center" v-html="icons[item.icon]"></span>
        <span>{{ item.label }}</span>
      </NuxtLink>
      <button @click="handleLogout" class="w-full text-left flex items-center gap-3 px-3 py-2 rounded-md text-red-400 hover:bg-primary-700">
        <span class="inline-flex items-center" v-html="icons.logout"></span>
        <span>Logout</span>
      </button>
    </div>
  </div>

  <!-- Desktop sidebar -->
  <aside :class="['hidden md:flex md:flex-col md:bg-primary-900 md:border-r md:border-primary-800 md:text-primary-50', props.collapsed ? 'md:w-20' : 'md:w-64']">
    <div :class="['px-4 h-14 flex items-center border-b border-primary-800', props.collapsed ? 'justify-center' : '']">
      <NuxtLink to="/" class="inline-flex items-center gap-2">
        <img :src="props.collapsed ? '/images/findsouth.png' : '/images/logo-white.png'" alt="FindSouth" class="h-8 w-auto " />
      </NuxtLink>
    </div>
    <nav class="flex-1 px-2 pt-4 space-y-1">
      <NuxtLink
        v-for="item in menuItems"
        :key="item.to"
        :to="item.to"
        :class="[linkBase, props.collapsed ? 'justify-center gap-0 px-0' : '', isActive(item.to) ? 'bg-primary-700 text-white font-semibold border-l-2 border-primary-400' : 'text-primary-100 hover:bg-primary-700']"
        :title="item.label"
      >
        <span class="inline-flex items-center" v-html="icons[item.icon]"></span>
        <span v-if="!props.collapsed">{{ item.label }}</span>
      </NuxtLink>
    </nav>
    <div class="border-t border-primary-800 p-2 space-y-1">
      <NuxtLink
        v-for="item in bottomItems"
        :key="item.to"
        :to="item.to"
        :class="[linkBase, props.collapsed ? 'justify-center gap-0 px-0' : '', isActive(item.to) ? 'bg-primary-700 text-white font-semibold border-l-2 border-primary-400' : 'text-primary-100 hover:bg-primary-700']"
        :title="item.label"
      >
        <span v-if="item.to === '/dashboard/my-profile' && user?.profile_image_url" class="inline-flex items-center">
          <img :src="user?.profile_image_url" alt="Profile" :class="[props.collapsed ? 'h-6 w-6' : 'h-5 w-5', 'rounded-full object-cover border border-primary-400']" />
        </span>
        <span v-else class="inline-flex items-center" v-html="icons[item.icon]"></span>
        <span v-if="!props.collapsed">{{ item.label }}</span>
      </NuxtLink>
      <button @click="handleLogout" :class="['w-full text-left flex items-center gap-3 px-3 py-2 rounded-md text-red-400 hover:bg-primary-700', props.collapsed ? 'justify-center gap-0 px-0' : '']" :title="'Logout'">
        <span class="inline-flex items-center" v-html="icons.logout"></span>
        <span v-if="!props.collapsed">Logout</span>
      </button>
    </div>
  </aside>
</template>
