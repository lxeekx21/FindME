<script setup lang="ts">
definePageMeta({ layout: 'dashboard', roles: ['user'] })
useHead({ title: 'My Submissions' })

const { accessToken } = useAuth()
const { apiBase } = useRuntimeConfig().public

interface SubmissionRow {
  id: number
  title: string
  full_name: string
  status: string
  created_at: string
  images?: string[] | null
}

const loading = ref(false)
const error = ref('')
const submissions = ref<SubmissionRow[]>([])

const fetchMine = async () => {
  if (!accessToken.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await $fetch<SubmissionRow[]>('/submissions/mine', {
      baseURL: apiBase,
      headers: { Authorization: `Bearer ${accessToken.value}` },
    })
    submissions.value = res
  } catch (err: any) {
    error.value = err?.data?.detail || 'Failed to load your submissions.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchMine)
watch(accessToken, (v) => { if (v) fetchMine() })

// Filters & pagination (copied style/behavior from user-accounts.vue)
const search = ref('')
const statusFilter = ref<'all' | 'pending' | 'rejected' | 'published' | 'found_alive' | 'found_dead'>('all')
const page = ref(1)
const pageSize = ref(10)

const statusClass = (status: string) => {
  const s = (status || '').toLowerCase()
  switch (s) {
    case 'published':
      return 'bg-emerald-100 text-emerald-800'
    case 'rejected':
      return 'bg-red-100 text-red-800'
    case 'found_alive':
      return 'bg-blue-100 text-blue-800'
    case 'found_dead':
      return 'bg-slate-200 text-slate-800'
    case 'pending':
      return 'bg-orange-100 text-orange-800'
    default:
      return 'bg-amber-100 text-amber-800'
  }
}

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return submissions.value.filter(s => {
    const matchesQuery = !q || [
      s.title,
      s.full_name,
      s.status,
      new Date(s.created_at).toLocaleDateString(),
    ].some(v => (v || '').toString().toLowerCase().includes(q))

    const matchesStatus = statusFilter.value === 'all' || (s.status || '').toLowerCase() === statusFilter.value
    return matchesQuery && matchesStatus
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))
watch([filtered, pageSize], () => { page.value = 1 })

const paged = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

// Resolve image URL: prefix apiBase for relative paths; use fallback if empty
const resolveImg = (url?: string | null) => {
  const fallback = '/images/logo-black.png'
  if (!url) return fallback
  const u = String(url)
  if (u.startsWith('http://') || u.startsWith('https://') || u.startsWith('data:')) return u
  const base = (apiBase || '').replace(/\/$/, '')
  const path = u.startsWith('/') ? u : `/${u}`
  return base ? `${base}${path}` : path
}
</script>

<template>
  <div class="space-y-4">
    <div v-if="error" class="rounded-md bg-red-50 p-3 text-red-700">{{ error }}</div>

    <!-- Filters -->
    <div class="bg-white border border-neutral-200 rounded-md p-3 flex flex-col md:flex-row gap-3 md:items-center md:justify-between">
      <div class="flex-1 flex gap-2">
        <input v-model="search" type="text" placeholder="Search title, name, status" class="w-full md:max-w-sm rounded-md border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
        <select v-model="statusFilter" class="rounded-md border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
          <option value="all">All status</option>
          <option value="pending">Pending</option>
          <option value="rejected">Rejected</option>
          <option value="published">Published</option>
          <option value="found_alive">Found (Alive)</option>
          <option value="found_dead">Found (Deceased)</option>
        </select>
      </div>
      <div class="flex items-center gap-2">
        <label class="text-sm text-neutral-600">Rows</label>
        <select v-model.number="pageSize" class="rounded-md border border-neutral-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
          <option :value="5">5</option>
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto bg-white border border-neutral-200 rounded-md">
      <table class="min-w-full divide-y divide-neutral-200">
        <thead class="bg-neutral-50">
          <tr>
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">#</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">Title</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">Person</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">Status</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">Created</th>
            <th class="px-4 py-2 text-right text-xs font-medium text-neutral-600 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-neutral-200" v-if="!loading">
          <tr v-for="(s, idx) in paged" :key="s.id" class="hover:bg-neutral-50/50">
            <td class="px-4 py-2 text-sm text-neutral-600">{{ (page - 1) * pageSize + idx + 1 }}</td>
            <td class="px-4 py-2 text-sm text-neutral-900 font-medium">{{ s.title }}</td>
            <td class="px-4 py-2 text-sm">
              <div class="flex items-center gap-3">
                <img :src="resolveImg(s.images && s.images.length ? s.images[0] : undefined)" class="h-8 w-8 rounded-4xl object-cover" />
                <div class="text-neutral-800">{{ s.full_name }}</div>
              </div>
            </td>
            <td class="px-4 py-2 text-sm">
              <span :class="[statusClass(s.status), 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium']">
                {{ s.status }}
              </span>
            </td>
            <td class="px-4 py-2 text-sm text-neutral-700">{{ new Date(s.created_at).toLocaleString() }}</td>
            <td class="px-4 py-2 text-sm">
              <div class="flex items-center justify-end gap-2 flex-wrap">
                <NuxtLink v-if="['published','found_alive','found_dead'].includes((s.status || '').toLowerCase())" :to="`/submissions/${s.id}`" class="inline-flex items-center whitespace-nowrap px-2.5 py-1 md:px-3 md:py-1.5 rounded-md bg-primary text-white text-xs hover:bg-primary-700">View</NuxtLink>
              </div>
            </td>
          </tr>
          <tr v-if="!paged.length">
            <td colspan="6" class="px-4 py-6 text-center text-sm text-neutral-500">No submissions found.</td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr>
            <td colspan="6" class="px-4 py-6 text-center text-sm text-neutral-500">Loading...</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between">
      <div class="text-sm text-neutral-600">Page {{ page }} of {{ totalPages }}</div>
      <div class="inline-flex gap-2">
        <button class="px-3 py-1.5 rounded-md border text-sm disabled:opacity-50" :disabled="page <= 1" @click="page = 1">First</button>
        <button class="px-3 py-1.5 rounded-md border text-sm disabled:opacity-50" :disabled="page <= 1" @click="page = page - 1">Prev</button>
        <button class="px-3 py-1.5 rounded-md border text-sm disabled:opacity-50" :disabled="page >= totalPages" @click="page = page + 1">Next</button>
        <button class="px-3 py-1.5 rounded-md border text-sm disabled:opacity-50" :disabled="page >= totalPages" @click="page = totalPages">Last</button>
      </div>
    </div>
  </div>
</template>
