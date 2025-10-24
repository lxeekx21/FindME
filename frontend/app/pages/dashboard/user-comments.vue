<script setup lang="ts">
interface Comment {
  id: number
  submission_id: number
  user_id?: number | null
  body: string
  image_url?: string | null
  status: 'pending' | 'approved' | 'rejected'
  rejection_reason?: string | null
  created_at: string
}

definePageMeta({ layout: 'dashboard', auth: 'admin' })

const { $api, isApiLoading } = useApi()
const router = useRouter()

const status = ref<string | null>(null) // null = all
const comments = ref<Comment[]>([])
// search query
const q = ref('')

// Computed displayed list (filters by search term; server still filters by status)
const displayed = computed(() => {
  const term = q.value.trim().toLowerCase()
  if (!term) return comments.value
  return comments.value.filter(c =>
    c.body.toLowerCase().includes(term) || String(c.submission_id).includes(term)
  )
})

const tabs = [
  { key: null, label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
]

function statusClass(s: string) {
  switch (s) {
    case 'approved': return 'bg-emerald-100 text-emerald-800'
    case 'rejected': return 'bg-red-100 text-red-800'
    case 'pending': return 'bg-amber-100 text-amber-800'
    default: return 'bg-neutral-100 text-neutral-800'
  }
}

async function load() {
  const q = status.value ? `?status=${status.value}` : ''
  const data = await $api<Comment[]>(`/comments/admin${q}`, { method: 'GET' })
  comments.value = data
}

function goToSubmission(id: number) {
  router.push(`/submissions/${id}`)
}

async function approve(id: number) {
  try {
    await $api<Comment>(`/comments/${id}/approve`, { method: 'POST' })
    await load()
  } catch (e) {
    alert('Failed to approve comment')
  }
}

async function reject(id: number) {
  const reason = prompt('Enter rejection reason (optional):') || ''
  try {
    await $api<Comment>(`/comments/${id}/reject`, { method: 'POST', body: { reason } })
    await load()
  } catch (e) {
    alert('Failed to reject comment')
  }
}

watch(status, load)
onMounted(load)
</script>

<template>
  <div class="bg-white">
    <div class="mx-auto  px-4 py-6 sm:px-6 lg:px-8">
      <h1 class="text-xl font-semibold text-neutral-900">User Comments</h1>
      <p class="text-sm text-neutral-600 mb-4">Review and moderate comments submitted by users.</p>

      <div class="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <div class="inline-flex items-center">
          <button
            v-for="t in tabs"
            :key="String(t.key)"
            @click="status = t.key as any"
            :class="['px-3 py-1.5 text-sm border rounded-none first:rounded-l-md last:rounded-r-md -ml-px first:ml-0 relative focus:z-10', status === t.key ? 'bg-primary text-white border-primary z-10' : 'bg-white text-neutral-700 border-neutral-300 hover:bg-neutral-50']"
          >
            {{ t.label }}
          </button>
        </div>
        <input v-model="q" type="text" placeholder="Search comments..." class="w-full sm:max-w-sm sm:ml-auto rounded-md border border-neutral-300 bg-white p-2 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-400" />
      </div>

      <div v-if="isApiLoading" class="rounded-md border border-neutral-200 p-4 text-neutral-600">Loading…</div>
      <div v-else-if="displayed.length === 0" class="rounded-md border border-neutral-200 p-4 text-neutral-600">No comments found.</div>

      <ul v-else class="space-y-3">
        <li v-for="c in displayed" :key="c.id" class="rounded-md border border-neutral-200 bg-white p-4">
          <div class="flex items-start gap-3">
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <div class="text-sm text-neutral-700">
                  Submission <button class="underline" @click="goToSubmission(c.submission_id)">#{{ c.submission_id }}</button>
                </div>
                <span :class="[statusClass(c.status), 'px-2 py-0.5 rounded text-xs font-medium capitalize']">{{ c.status }}</span>
              </div>
              <p class="mt-2 text-sm text-neutral-800 whitespace-pre-line">{{ c.body }}</p>
              <div v-if="c.image_url" class="mt-2">
                <img :src="c.image_url" alt="comment image" class="max-h-64 rounded" />
              </div>
              <div v-if="c.status === 'rejected' && c.rejection_reason" class="mt-2 text-xs text-red-700">Reason: {{ c.rejection_reason }}</div>
              <div class="mt-2 text-xs text-neutral-500">{{ new Date(c.created_at).toLocaleString() }}</div>

              <div class="mt-3 flex items-center gap-2">
                <button v-if="c.status === 'pending'" @click="approve(c.id)" class="rounded bg-emerald-600 text-white text-sm px-3 py-1.5 hover:bg-emerald-700">Approve</button>
                <!-- Allow rejecting even approved comments -->
                <button v-if="c.status !== 'rejected'" @click="reject(c.id)" class="rounded bg-red-600 text-white text-sm px-3 py-1.5 hover:bg-red-700">Reject</button>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
