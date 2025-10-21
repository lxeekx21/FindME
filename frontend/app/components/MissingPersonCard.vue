<script setup lang="ts">
import moment from 'moment'

interface Submission {
  id: number
  title: string
  full_name: string
  dob?: string | null
  gender?: string | null
  race?: string | null
  province?: string | null
  description?: string | null
  status: string
  last_seen_address?: string | null
  images?: string[] | null
  created_at: string
}

const props = defineProps<{ submission: Submission }>()

const emit = defineEmits<{ (e: 'view', id: number): void }>()

const { apiBase } = useRuntimeConfig().public

function toAbsoluteUrl(url?: string | null): string | null {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/')) return `${apiBase?.replace(/\/$/, '')}${url}`
  return url
}

const imageUrl = computed(() => {
  const raw = props.submission.images?.[0]
  const abs = toAbsoluteUrl(raw)
  return (
    abs || 'https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1200&auto=format&fit=crop'
  )
})

function provinceLabel(code?: string | null): string {
  if (!code) return 'Unknown'
  return code
    .split('_')
    .map(s => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}

function calcAge(dob?: string | null): number | null {
  if (!dob) return null
  const d = new Date(dob)
  if (isNaN(d.getTime())) return null
  const now = new Date()
  let age = now.getFullYear() - d.getFullYear()
  const m = now.getMonth() - d.getMonth()
  if (m < 0 || (m === 0 && now.getDate() < d.getDate())) age--
  return age
}

const isFound = computed(() => (props.submission.status || '').toLowerCase() === 'found')
</script>

<template>
  <div class="group overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-sm transition hover:shadow-md cursor-pointer">
    <NuxtLink
      :to="`/submissions/${submission.id}`"
      class="relative block aspect-[4/3] w-full overflow-hidden bg-neutral-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-neutral-400"
      :aria-label="`View details for ${submission.full_name}`"
    >
      <img :src="imageUrl" :alt="submission.full_name" class="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]" />
      <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
      <div class="absolute bottom-0 left-0 right-0 p-3 text-white">
        <div class="text-sm uppercase tracking-wide opacity-90">{{ provinceLabel(submission.province) }}</div>
        <div class="text-lg font-semibold leading-tight">{{ submission.full_name }}</div>
        <div class="text-xs opacity-90" v-if="calcAge(submission.dob) !== null">Age: {{ calcAge(submission.dob) }}</div>
      </div>
    </NuxtLink>
    <div class="p-3">
      <p class="line-clamp-2 text-sm text-neutral-700 min-h-[2.5rem]">{{ submission.description || 'No description provided.' }}</p>

      <!-- Status/location row: show Found label if status is found; otherwise show Last seen address -->
      <div v-if="isFound" class="mt-2 inline-flex items-center gap-1 rounded-md bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-3.5 w-3.5">
          <path fill-rule="evenodd" d="M16.704 5.29a1 1 0 0 1 .006 1.414l-7.25 7.333a1 1 0 0 1-1.442.006L3.29 9.29a1 1 0 1 1 1.414-1.414l4.02 4.02 6.536-6.593a1 1 0 0 1 1.414-.006Z" clip-rule="evenodd" />
        </svg>
        Found
      </div>
      <div v-else-if="submission.last_seen_address" class="mt-2 flex items-center gap-1 text-xs text-neutral-600">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-3.5 w-3.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 21c-4.97-4.97-7.455-8.045-7.455-11.182a7.455 7.455 0 1 1 14.91 0C19.455 12.955 17 16.03 12 21Zm0 0c-2.485-2.485-3.727-4.227-3.727-5.636A3.727 3.727 0 1 1 12 19.364Z" />
        </svg>
        <span class="truncate">Last seen: {{ submission.last_seen_address }}</span>
      </div>

      <div class="mt-3 flex  justify-end">
        <span class="text-xs  text-neutral-500">{{  moment(submission.created_at).format('DD/MMM/YYYY') }} </span>
      </div>
    </div>
  </div>
</template>
