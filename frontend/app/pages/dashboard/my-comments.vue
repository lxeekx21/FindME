<script setup lang="ts">
import moment from 'moment'
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

type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected'
type SortOrder = 'new' | 'old'

decodeURI

definePageMeta({ layout: 'dashboard', auth: 'user' })

const { $api, isApiLoading, lastError } = useApi()
const router = useRouter()

const comments = ref<Comment[]>([])

// UI state: search, filter, sort
const q = ref('')
const status = ref<StatusFilter>('all')
const sort = ref<SortOrder>('new')

const displayed = computed(() => {
  let list = [...comments.value]
  // filter by status
  if (status.value !== 'all') {
    list = list.filter(c => c.status === status.value)
  }
  // search in body and submission id
  const term = q.value.trim().toLowerCase()
  if (term) {
    list = list.filter(c =>
      c.body.toLowerCase().includes(term) || String(c.submission_id).includes(term)
    )
  }
  // sort
  list.sort((a, b) => {
    const da = new Date(a.created_at).getTime()
    const db = new Date(b.created_at).getTime()
    return sort.value === 'new' ? db - da : da - db
  })
  return list
})

async function load() {
  try {
    const data = await $api<Comment[]>(`/comments/mine`, { method: 'GET' })
    comments.value = data
  } catch (e) {
    console.error('Failed to load my comments', e)
  }
}

function statusClass(s: string) {
  switch (s) {
    case 'approved': return 'bg-emerald-100 text-emerald-800'
    case 'rejected': return 'bg-red-100 text-red-800'
    case 'pending': return 'bg-amber-100 text-amber-800'
    default: return 'bg-neutral-100 text-neutral-800'
  }
}

function goToSubmission(id: number) {
  router.push(`/submissions/${id}`)
}

onMounted(load)
</script>

<template>
  <div class="bg-white">
    <div class="mx-auto  px-4 py-6 sm:px-6 lg:px-8">
      <h1 class="text-xl font-semibold text-neutral-900">My Comments</h1>
      <p class="text-sm text-neutral-600 mb-4">View all comments you have submitted and their moderation status.</p>

      <!-- Controls: search, status filter, sort -->
      <div class="mb-8 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <input v-model="q" type="text" placeholder="Search your comments..." class="w-full sm:max-w-sm rounded-md border border-neutral-300 bg-white p-2 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-400" />
        <select v-model="status" class="rounded-md border border-neutral-300 bg-white p-2 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-400">
          <option value="all">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <select v-model="sort" class="rounded-md border border-neutral-300 bg-white p-2 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-400">
          <option value="new">Newest first</option>
          <option value="old">Oldest first</option>
        </select>
      </div>

      <div v-if="isApiLoading" class="rounded-md border border-neutral-200 p-4 text-neutral-600">Loading…</div>
      <div v-else-if="comments.length === 0" class="rounded-md border border-neutral-200 p-4 text-neutral-600">You haven't posted any comments yet.</div>

      <ul v-else class="space-y-3">
        <li v-for="c in displayed" :key="c.id" class="rounded-md border border-neutral-200 bg-white p-4">
          <div class="flex items-start gap-3">
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <div class="text-sm text-neutral-700">On submission <button class="underline" @click="goToSubmission(c.submission_id)">#{{ c.submission_id }}</button></div>
                <span :class="[statusClass(c.status), 'px-2 py-0.5 rounded text-xs font-medium capitalize']">{{ c.status }}</span>
              </div>
              <p class="mt-2 text-sm text-neutral-800 whitespace-pre-line">{{ c.body }}</p>
              <div v-if="c.image_url" class="mt-2">
                <img :src="c.image_url" alt="comment image" class="max-h-64 rounded" />
              </div>
              <div v-if="c.status === 'rejected' && c.rejection_reason" class="mt-2 text-xs text-red-700">Reason: {{ c.rejection_reason }}</div>
              <div class="mt-2 text-xs text-neutral-500">{{ moment(c.created_at).fromNow() }}</div>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
