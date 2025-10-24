<script setup lang="ts">
definePageMeta({ layout: 'dashboard', roles: ['admin'] })
useHead({ title: 'User Accounts' })

const { accessToken } = useAuth()
const { apiBase } = useRuntimeConfig().public

interface Role { id: number; name: string }
interface UserRow {
  id: number
  email: string
  first_name?: string
  last_name?: string
  phone?: string | null
  profile_image_url?: string | null
  is_active: boolean
  dob?: string | null
  gender?: string | null
  roles: Role[]
}

const loading = ref(false)
const error = ref('')
const users = ref<UserRow[]>([])

const fetchData = async () => {
  if (!accessToken.value) return
  loading.value = true
  error.value = ''
  try {
    const u = await $fetch<UserRow[]>('/admin/users', { baseURL: apiBase, headers: { Authorization: `Bearer ${accessToken.value}` } })
    users.value = u
  } catch (err: any) {
    error.value = err?.data?.detail || 'Failed to load users.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
watch(accessToken, (v) => { if (v) fetchData() })

const currentRoleName = (u: UserRow) => (u.roles?.[0]?.name || 'user')

// Filters
const search = ref('')
const roleFilter = ref<'all' | 'admin' | 'user'>('all')
const statusFilter = ref<'all' | 'active' | 'disabled'>('all')

const page = ref(1)
const pageSize = ref(10)

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return users.value.filter(u => {
    const matchesQuery = !q || [
      u.email,
      `${u.first_name || ''} ${u.last_name || ''}`,
      u.phone || ''
    ].some(v => (v || '').toLowerCase().includes(q))

    const roleName = currentRoleName(u)
    const matchesRole = roleFilter.value === 'all' || roleFilter.value === roleName

    const matchesStatus = statusFilter.value === 'all' ||
      (statusFilter.value === 'active' && u.is_active) ||
      (statusFilter.value === 'disabled' && !u.is_active)

    return matchesQuery && matchesRole && matchesStatus
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))
watch([filtered, pageSize], () => { page.value = 1 })

const paged = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

// Edit modal (Tailwind only: toggles for Active and Admin)
const isOpen = ref(false)
const editing = ref<UserRow | null>(null)

const form = reactive({
  is_active: true,
  is_admin: false,
})

const openEdit = (u: UserRow) => {
  editing.value = u
  form.is_active = !!u.is_active
  form.is_admin = currentRoleName(u) === 'admin'
  isOpen.value = true
}

const saving = ref(false)
const save = async () => {
  if (!editing.value || !accessToken.value) return
  saving.value = true
  try {
    // 1) Update is_active if changed
    if (form.is_active !== editing.value.is_active) {
      const updated = await $fetch<UserRow>(`/admin/users/${editing.value.id}`, {
        baseURL: apiBase,
        method: 'PATCH',
        headers: { Authorization: `Bearer ${accessToken.value}` },
        body: { is_active: form.is_active },
      })
      Object.assign(editing.value, updated)
    }

    // 2) Update role if changed (admin/user)
    const desiredRole = form.is_admin ? 'admin' : 'user'
    if (desiredRole !== currentRoleName(editing.value)) {
      const updated = await $fetch<UserRow>(`/admin/users/${editing.value.id}/role`, {
        baseURL: apiBase,
        method: 'PUT',
        headers: { Authorization: `Bearer ${accessToken.value}` },
        body: { role_name: desiredRole },
      })
      Object.assign(editing.value, updated)
    }

    // Reflect changes in list
    const idx = users.value.findIndex(x => x.id === editing.value!.id)
    if (idx !== -1 && editing.value) users.value[idx] = { ...editing.value }

    isOpen.value = false
  } catch (err: any) {
    alert(err?.data?.detail || 'Failed to save changes')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div v-if="error" class="rounded-md bg-red-50 p-3 text-red-700">{{ error }}</div>

    <!-- Filters -->
    <div class="bg-white border border-neutral-200 rounded-md p-3 flex flex-col md:flex-row gap-3 md:items-center md:justify-between">
      <div class="flex-1 flex gap-2">
        <input v-model="search" type="text" placeholder="Search name, email, phone" class="w-full md:max-w-sm rounded-md border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400" />
        <select v-model="roleFilter" class="rounded-md border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
          <option value="all">All roles</option>
          <option value="admin">Admin</option>
          <option value="user">User</option>
        </select>
        <select v-model="statusFilter" class="rounded-md border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400">
          <option value="all">All status</option>
          <option value="active">Active</option>
          <option value="disabled">Disabled</option>
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
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">User</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">Email</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">Phone</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">Role</th>
            <th class="px-4 py-2 text-left text-xs font-medium text-neutral-600 uppercase tracking-wider">Status</th>
            <th class="px-4 py-2 text-right text-xs font-medium text-neutral-600 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-neutral-200" v-if="!loading">
          <tr v-for="(u, idx) in paged" :key="u.id" class="hover:bg-neutral-50/50">
            <td class="px-4 py-2 text-sm text-neutral-600">{{ (page - 1) * pageSize + idx + 1 }}</td>
            <td class="px-4 py-2 text-sm">
              <div class="flex items-center gap-3">
                <img :src="u.profile_image_url || '/images/logo-black.png'" class="h-8 w-8 rounded-full object-cover border border-neutral-300" />
                <div>
                  <div class="font-medium text-neutral-900">{{ (u.first_name || u.last_name) ? `${u.first_name || ''} ${u.last_name || ''}`.trim() : '—' }}</div>
                </div>
              </div>
            </td>
            <td class="px-4 py-2 text-sm text-neutral-700">{{ u.email }}</td>
            <td class="px-4 py-2 text-sm text-neutral-700">{{ u.phone || '—' }}</td>
            <td class="px-4 py-2 text-sm">
              <span :class="[currentRoleName(u) === 'admin' ? 'bg-emerald-100 text-emerald-800' : 'bg-orange-100 text-orange-800', 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium']">
                {{ currentRoleName(u) }}
              </span>
            </td>
            <td class="px-4 py-2 text-sm">
              <span :class="[u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800', 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium']">
                {{ u.is_active ? 'Active' : 'Disabled' }}
              </span>
            </td>
            <td class="px-4 py-2 text-sm text-right">
              <button @click="openEdit(u)" class="inline-flex items-center px-3 py-1.5 rounded-md bg-primary text-white text-xs hover:bg-primary-700">Edit</button>
            </td>
          </tr>
          <tr v-if="!paged.length">
            <td colspan="7" class="px-4 py-6 text-center text-sm text-neutral-500">No users found.</td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr>
            <td colspan="7" class="px-4 py-6 text-center text-sm text-neutral-500">Loading...</td>
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

    <!-- Modal (Tailwind) -->
    <transition name="fade">
      <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/40" @click="isOpen = false"></div>
        <div class="relative z-10 w-full max-w-md bg-white rounded-md shadow-lg border border-neutral-200 p-4">
          <div class="text-lg font-medium mb-2">Edit user</div>
          <div v-if="editing" class="space-y-4">
            <div class="flex items-center gap-3">
              <img :src="editing.profile_image_url || '/images/logo-black.png'" class="h-10 w-10 rounded-full object-cover border border-neutral-300" />
              <div>
                <div class="font-medium text-neutral-900">{{ (editing.first_name || editing.last_name) ? `${editing.first_name || ''} ${editing.last_name || ''}`.trim() : editing.email }}</div>
                <div class="text-xs text-neutral-500">{{ editing.email }}</div>
              </div>
            </div>

            <div class="space-y-2">
              <label class="flex items-center gap-2">
                <input type="checkbox" v-model="form.is_active" class="h-4 w-4 rounded border-neutral-300 text-primary focus:ring-primary-500" />
                <span class="text-sm text-neutral-800">Active</span>
              </label>
              <label class="flex items-center gap-2">
                <input type="checkbox" v-model="form.is_admin" class="h-4 w-4 rounded border-neutral-300 text-primary focus:ring-primary-500" />
                <span class="text-sm text-neutral-800">Admin</span>
              </label>
            </div>

            <div class="flex justify-end gap-2 pt-2">
              <button @click="isOpen = false" class="px-3 py-1.5 rounded-md border text-sm">Cancel</button>
              <button @click="save" :disabled="saving" class="px-3 py-1.5 rounded-md bg-primary text-white text-sm disabled:opacity-50">{{ saving ? 'Saving...' : 'Save' }}</button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
