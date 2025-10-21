<script setup lang="ts">
import moment from 'moment'
interface Submission {
  id: number
  title: string
  full_name: string
  dob?: string | null
  gender?: string | null
  race?: string | null
  height?: number | null
  weight?: number | null
  province?: string | null
  description?: string | null
  status: string
  last_seen_address?: string | null
  last_seen_place_id?: string | null
  last_seen_lat?: number | null
  last_seen_lng?: number | null
  images?: string[] | null
  created_at: string
}


definePageMeta({ auth: 'public' })

const route = useRoute()
const router = useRouter()
const { $api, isApiLoading, lastError } = useApi()
const { apiBase } = useRuntimeConfig().public
const publicCfg = useRuntimeConfig().public as any
const apiKey: string | undefined = publicCfg.googleMapsApiKey
const mapId: string | undefined = publicCfg.googleMapsMapId

// Auth (for commenting rules)
const { isAuthenticated, user, initializeAuth } = useAuth()
await initializeAuth()
const isAdmin = computed(() => !!user.value?.roles?.some(r => r.name?.toLowerCase() === 'admin'))
const canComment = computed(() => isAuthenticated.value && !isAdmin.value)

const submission = ref<Submission | null>(null)

// Image gallery state
const currentIndex = ref(0)
const hasMultiple = computed(() => (submission.value?.images?.length || 0) > 1)
const canPrev = computed(() => hasMultiple.value && currentIndex.value > 0)
const canNext = computed(() => hasMultiple.value && currentIndex.value < ((submission.value?.images?.length || 0) - 1))

const currentImage = computed(() => {
  const list = submission.value?.images || []
  const raw = list[currentIndex.value]
  const abs = toAbsoluteUrl(raw)
  return (
    abs || 'https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1200&auto=format&fit=crop'
  )
})

function prevImage() {
  if (canPrev.value) currentIndex.value--
}
function nextImage() {
  if (canNext.value) currentIndex.value++
}

function toAbsoluteUrl(url?: string | null): string | null {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/')) return `${apiBase?.replace(/\/$/, '')}${url}`
  return url
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

function provinceLabel(code?: string | null): string {
  if (!code) return 'Unknown'
  return code
    .split('_')
    .map(s => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}

function raceLabel(code?: string | null): string {
  if (!code) return 'Unknown'
  return code
    .split('_')
    .map(s => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ')
}

async function fetchOne() {
  try {
    const id = Number(route.params.id)
    if (!id) return
    const data = await $api<Submission>(`/submissions/${id}`, { method: 'GET', noAuth: true })
    submission.value = data
  } catch (e) {
    console.error('Failed to load submission', e)
  }
}

function statusClass(status?: string | null): string {
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

// Age-based alert tiers
const reportedFromNow = computed(() => submission.value ? moment(submission.value.created_at).fromNow() : '')
const age = computed(() => {
  const d = submission.value?.created_at
  if (!d) return { hours: 0, days: 0, months: 0 }
  const m = moment(d)
  return {
    hours: moment().diff(m, 'hours'),
    days: moment().diff(m, 'days'),
    months: moment().diff(m, 'months'),
  }
})
// Tiers: lt72h, h72_to_30d, m1_to_12, gt12m
const alertTier = computed(() => {
  const h = age.value.hours
  const d = age.value.days
  const mo = age.value.months
  if (mo >= 12) return 'gt12m' as const
  if (mo >= 1) return 'm1_to_12' as const
  if (d >= 3) return 'h72_to_30d' as const
  return 'lt72h' as const
})

// For cases older than a year, provide milestone labels at 5, 10, 15, and 20 years
const yearsSinceReport = computed(() => {
  const d = submission.value?.created_at
  if (!d) return 0
  return moment().diff(moment(d), 'years')
})
const yearThreshold = computed(() => {
  const y = yearsSinceReport.value
  if (y >= 20) return 20
  if (y >= 15) return 15
  if (y >= 10) return 10
  if (y >= 5) return 5
  return 1
})
const gt12Label = computed(() => `This case is over ${yearThreshold.value} year${yearThreshold.value > 1 ? 's' : ''} old`)
const showAgeProgressionBtn = computed(() => yearsSinceReport.value >= 5)
const isGeneratingAge = ref(false)
const showImageModal = ref(false)
const modalImageSrc = ref<string | null>(null)
function openImageModal() { modalImageSrc.value = currentImage.value || null; showImageModal.value = true }
function closeImageModal() { showImageModal.value = false; modalImageSrc.value = null }
function onKeydown(e: KeyboardEvent) { if (e.key === 'Escape') closeImageModal() }

async function handleAgeProgressionClick() {
  if (!submission.value) return
  try {
    isGeneratingAge.value = true
    const id = Number(route.params.id)
    const years = yearsSinceReport.value
    const resp = await $api<{ url: string }>(`/submissions/${id}/age-progression?years=${years}`, { method: 'GET', noAuth: true })
    if (resp?.url) {
      // Show in modal only, do not add to gallery
      modalImageSrc.value = resp.url
      showImageModal.value = true
    } else {
      alert('Failed to generate age progression image.')
    }
  } catch (e) {
    console.error('Age progression error', e)
    alert('Failed to generate age progression image.')
  } finally {
    isGeneratingAge.value = false
  }
}
const contact = {
  police: '10111',
  email: 'tips@findsouth.org',
  hotline: '+27 87 123 4567',
}

// Resolved status flags
const isFoundAlive = computed(() => (submission.value?.status || '').toLowerCase() === 'found_alive')
const isFoundDead = computed(() => (submission.value?.status || '').toLowerCase() === 'found_dead')

// COMMENTS
interface Comment {
  id: number
  submission_id: number
  user_id?: number | null
  body: string
  image_url?: string | null
  status: 'pending' | 'approved' | 'rejected'
  rejection_reason?: string | null
  created_at: string
  author_name?: string | null
  author_profile_image_url?: string | null
}

const comments = ref<Comment[]>([])
const newComment = ref('')
const imageFile = ref<File | null>(null)
const sending = ref(false)

async function fetchComments() {
  try {
    const id = Number(route.params.id)
    if (!id) return
    const list = await $api<Comment[]>(`/comments?submission_id=${id}`, { method: 'GET', noAuth: true })
    comments.value = list
  } catch (e) {
    console.error('Failed to load comments', e)
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  imageFile.value = (input.files && input.files[0]) ? input.files[0] : null
}

async function submitComment() {
  if (!canComment.value) { alert('You must be logged in with a regular account to comment.'); return }
  const id = Number(route.params.id)
  if (!id || !newComment.value.trim()) return
  sending.value = true
  try {
    const fd = new FormData()
    fd.append('submission_id', String(id))
    fd.append('body', newComment.value.trim())
    if (imageFile.value) fd.append('image', imageFile.value)
    await $api<Comment>(`/comments/`, { method: 'POST', body: fd as any })
    // Reset form and inform user that comment awaits approval
    newComment.value = ''
    imageFile.value = null
    await fetchComments()
    alert('Your comment was submitted and is awaiting admin approval.')
  } catch (e) {
    console.error('Failed to submit comment', e)
    alert('Failed to submit comment.')
  } finally {
    sending.value = false
  }
}


onMounted( async() => {
  window.addEventListener('keydown', onKeydown)
  await fetchOne();
  await fetchComments()

  useHead({ title: `${submission?.value?.full_name}'s Report` })
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
watch(() => route.params.id, () => { fetchOne(); fetchComments() })
watch(submission, () => { currentIndex.value = 0; setupMap() })

// Maps & Street View
const mapEl = ref<HTMLDivElement | null>(null)
const panoEl = ref<HTMLDivElement | null>(null)
let gmap: any = null
let panorama: any = null
let panoMap: any = null
let panoMarker: any = null
let marker: any = null
let mapsScriptLoaded = false
const streetViewAvailable = ref(true)

function ensureMapsScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (mapsScriptLoaded || (globalThis as any).google?.maps) {
      mapsScriptLoaded = true
      resolve()
      return
    }
    if (!apiKey) { resolve(); return } // Graceful: render fallback text if no key
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&libraries=places`
    script.async = true
    script.defer = true
    script.onload = () => { mapsScriptLoaded = true; resolve() }
    script.onerror = () => reject(new Error('Failed to load Google Maps'))
    document.head.appendChild(script)
  })
}

async function setupMap() {
  if (!submission.value) return
  await ensureMapsScript()
  const google = (globalThis as any).google
  if (!google?.maps) return
  if (!mapEl.value || !panoEl.value) return

  const lat = typeof submission.value.last_seen_lat === 'number' ? submission.value.last_seen_lat : -30.5595
  const lng = typeof submission.value.last_seen_lng === 'number' ? submission.value.last_seen_lng : 22.9375
  const hasPoint = typeof submission.value.last_seen_lat === 'number' && typeof submission.value.last_seen_lng === 'number'
  const center = { lat, lng }

  // Cleanup right panel before re-initializing
  try {
    if (panorama) { panorama.setVisible(false) }
  } catch {}
  try {
    if (panoEl.value) panoEl.value.innerHTML = ''
  } catch {}
  panorama = null
  panoMap = null
  try { if (panoMarker) panoMarker.setMap(null) } catch {}
  panoMarker = null

  gmap = new google.maps.Map(mapEl.value, {
    center,
    zoom: hasPoint ? 14 : 6,
    mapId: mapId || undefined,
    streetViewControl: true,
    mapTypeControl: true,
    fullscreenControl: true,
    zoomControl: true,
  })

  // Align initial angle/orientation for consistency across maps
  try { if (typeof gmap.setHeading === 'function') gmap.setHeading(0) } catch {}
  try { if (typeof gmap.setTilt === 'function') gmap.setTilt(0) } catch {}

  // Determine Street View availability and initialize right panel accordingly
  try {
    const sv = new google.maps.StreetViewService()
    if (hasPoint) {
      sv.getPanorama({ location: center, radius: 100 }, (data: any, status: any) => {
        const ok = status === google.maps.StreetViewStatus.OK || status === 'OK'
        streetViewAvailable.value = !!ok
        if (ok) {
          const baseHeading = (typeof gmap.getHeading === 'function' && gmap.getHeading() != null) ? gmap.getHeading() : 0
          panorama = new google.maps.StreetViewPanorama(panoEl.value, {
            position: center,
            pov: { heading: baseHeading, pitch: 0 },
            visible: true,
            addressControl: true,
            linksControl: true,
            panControl: true,
            zoomControl: true,
            fullscreenControl: true,
          })
          gmap.setStreetView(panorama)
        } else {
          // Fallback: show satellite map on the right so user can roam
          panoMap = new google.maps.Map(panoEl.value, {
            center,
            zoom: hasPoint ? 16 : 8,
            mapId: mapId || undefined,
            mapTypeId: google.maps.MapTypeId.SATELLITE,
            streetViewControl: true,
            mapTypeControl: true,
            fullscreenControl: true,
            zoomControl: true,
          })
          // Sync right map orientation and zoom with left map
          try { if (typeof panoMap.setHeading === 'function') panoMap.setHeading((typeof gmap.getHeading === 'function' && gmap.getHeading() != null) ? gmap.getHeading() : 0) } catch {}
          try { if (typeof panoMap.setTilt === 'function') panoMap.setTilt((typeof gmap.getTilt === 'function' && gmap.getTilt() != null) ? gmap.getTilt() : 0) } catch {}
          try { if (typeof panoMap.setZoom === 'function') panoMap.setZoom((typeof gmap.getZoom === 'function' && gmap.getZoom() != null) ? gmap.getZoom() : (hasPoint ? 16 : 8)) } catch {}
          try { if (panoMarker) panoMarker.setMap(null) } catch {}
          panoMarker = new google.maps.Marker({
            map: panoMap,
            position: center,
            draggable: false,
            title: submission.value.full_name,
          })
        }
      })
    } else {
      streetViewAvailable.value = false
      panoMap = new google.maps.Map(panoEl.value, {
        center,
        zoom: 6,
        mapId: mapId || undefined,
        mapTypeId: google.maps.MapTypeId.SATELLITE,
        streetViewControl: true,
        mapTypeControl: true,
        fullscreenControl: true,
        zoomControl: true,
      })
      // Sync right map orientation and zoom with left map
      try { if (typeof panoMap.setHeading === 'function') panoMap.setHeading((typeof gmap.getHeading === 'function' && gmap.getHeading() != null) ? gmap.getHeading() : 0) } catch {}
      try { if (typeof panoMap.setTilt === 'function') panoMap.setTilt((typeof gmap.getTilt === 'function' && gmap.getTilt() != null) ? gmap.getTilt() : 0) } catch {}
      try { if (typeof panoMap.setZoom === 'function') panoMap.setZoom((typeof gmap.getZoom === 'function' && gmap.getZoom() != null) ? gmap.getZoom() : 6) } catch {}
      try { if (panoMarker) panoMarker.setMap(null) } catch {}
      panoMarker = new google.maps.Marker({
        map: panoMap,
        position: center,
        draggable: false,
        title: submission.value.full_name,
      })
    }
  } catch {
    streetViewAvailable.value = false
    panoMap = new google.maps.Map(panoEl.value, {
      center,
      zoom: hasPoint ? 16 : 8,
      mapId: mapId || undefined,
      mapTypeId: (globalThis as any).google?.maps?.MapTypeId?.SATELLITE,
      streetViewControl: true,
      mapTypeControl: true,
      fullscreenControl: true,
      zoomControl: true,
    })
    try { if (panoMarker) panoMarker.setMap(null) } catch {}
    panoMarker = new google.maps.Marker({
      map: panoMap,
      position: center,
      draggable: false,
      title: submission.value.full_name,
    })
  }

  // Final post-init sync to ensure same angle/zoom once maps finish loading
  try {
    (globalThis as any).google?.maps?.event?.addListenerOnce?.(gmap, 'idle', () => {
      try { if (typeof gmap.setHeading === 'function') gmap.setHeading(0) } catch {}
      try { if (typeof gmap.setTilt === 'function') gmap.setTilt(0) } catch {}
      const h = (typeof gmap.getHeading === 'function' && gmap.getHeading() != null) ? gmap.getHeading() : 0
      const t = (typeof gmap.getTilt === 'function' && gmap.getTilt() != null) ? gmap.getTilt() : 0
      const z = (typeof gmap.getZoom === 'function' && gmap.getZoom() != null) ? gmap.getZoom() : (hasPoint ? 14 : 6)
      try { if (panorama) panorama.setPov({ heading: h, pitch: 0 }) } catch {}
      try {
        if (panoMap) {
          if (typeof panoMap.setHeading === 'function') panoMap.setHeading(h)
          if (typeof panoMap.setTilt === 'function') panoMap.setTilt(t)
          if (typeof panoMap.setZoom === 'function') panoMap.setZoom(z)
        }
      } catch {}
    })
  } catch {}
  try {
    if (panoMap && (globalThis as any).google?.maps?.event?.addListenerOnce) {
      (globalThis as any).google.maps.event.addListenerOnce(panoMap, 'idle', () => {
        const h = (typeof gmap.getHeading === 'function' && gmap.getHeading() != null) ? gmap.getHeading() : 0
        const t = (typeof gmap.getTilt === 'function' && gmap.getTilt() != null) ? gmap.getTilt() : 0
        const z = (typeof gmap.getZoom === 'function' && gmap.getZoom() != null) ? gmap.getZoom() : (hasPoint ? 14 : 6)
        try { if (typeof panoMap.setHeading === 'function') panoMap.setHeading(h) } catch {}
        try { if (typeof panoMap.setTilt === 'function') panoMap.setTilt(t) } catch {}
        try { if (typeof panoMap.setZoom === 'function') panoMap.setZoom(z) } catch {}
      })
    }
  } catch {}

  // Use the first image as the marker icon
  // Normal default marker (not draggable) at last seen position
  marker = new google.maps.Marker({
    map: gmap,
    position: center,
    draggable: false,
    title: submission.value.full_name,
  })

  // Info window indicating last seen location and when
  const lastSeenAgo = reportedFromNow.value || 'some time ago'
  const addr = submission.value.last_seen_address
  const infoHtml = `<div style="font-size:12px;line-height:1.4;max-width:220px;">
    <strong>Last seen location</strong><br/>
    ${addr ? `<div>${addr}</div>` : ''}
    <div style="color:#666;">${lastSeenAgo}</div>
  </div>`
  const infoWindow = new google.maps.InfoWindow({ content: infoHtml })
  infoWindow.open({ anchor: marker, map: gmap })
  marker.addListener('click', () => infoWindow.open({ anchor: marker, map: gmap }))

  // Keep Street View synced to marker position
  if (panorama) panorama.setPosition(center)
}

</script>

<template>
  <div class="bg-white">
    <div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <button class="mb-4 cursor-pointer inline-flex items-center gap-2 text-sm text-neutral-600 hover:text-neutral-900" @click="router.back()">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-4 w-4">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
        Back
      </button>

      <div v-if="!submission && isApiLoading" class="rounded-lg border border-neutral-200 p-8 text-center text-neutral-600">Loading…</div>
      <div v-else-if="!submission" class="rounded-lg border border-red-200 bg-red-50 p-8 text-center text-red-700">Not found or was removed.</div>
      <div v-else class="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div>
          <div class="relative aspect-[4/3] overflow-hidden rounded-lg bg-neutral-100">
            <img :src="currentImage" :alt="submission.full_name" class="h-full w-full object-cover cursor-zoom-in" @click="openImageModal" title="Click to enlarge" />

            <!-- Vertical thumbnails on right -->
            <div
              v-if="submission.images && submission.images.length > 1"
              class="absolute right-2 top-2 bottom-2 z-10 flex w-20 flex-col gap-2 overflow-y-auto rounded-md"
              aria-label="Image thumbnails"
            >
              <button
                v-for="(img, idx) in submission.images"
                :key="idx"
                type="button"
                class="relative block h-16 w-20 overflow-hidden rounded-md border bg-white/70 backdrop-blur focus:outline-none focus:ring-2 focus:ring-neutral-400"
                @click.stop="currentIndex = idx"
                :aria-current="idx === currentIndex"
                :title="`View image ${idx + 1}`"
                :class="idx === currentIndex ? 'border-primary ring-2 ring-primary' : 'border-white/60 hover:border-white'"
              >
                <img :src="toAbsoluteUrl(img) || ''" :alt="`${submission.full_name} ${idx+1}`" class="h-full w-full object-cover" />
              </button>
            </div>

          </div>

        </div>

        <div>
          <h1 class="text-2xl font-bold text-neutral-900">{{ submission.full_name }}</h1>
          <p class="mt-1 text-neutral-600">{{ submission.title }}</p>
          <div class="mt-2">
            <span :class="[statusClass(submission.status), 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize']">
              {{ submission.status }}
            </span>
          </div>
          <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-neutral-700">
            <span v-if="calcAge(submission.dob) !== null">Age: <strong>{{ calcAge(submission.dob) }}</strong></span>
            <span v-if="submission.gender">Gender: <strong class="capitalize">{{ submission.gender }}</strong></span>
            <span v-if="submission.race">Race: <strong>{{ raceLabel(submission.race) }}</strong></span>
            <span v-if="submission.height">Height: <strong>{{ submission.height }} cm</strong></span>
            <span v-if="submission.weight">Weight: <strong>{{ submission.weight }} kg</strong></span>
            <span>Province: <strong>{{ provinceLabel(submission.province) }}</strong></span>
          </div>

          <div class="mt-4 rounded-md bg-neutral-50 py-3 text-sm text-neutral-700" v-if="submission.last_seen_address">
            <div class="mb-1 font-medium text-neutral-900">Last seen</div>
            <div class="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-4 w-4 text-neutral-700">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 21c-4.97-4.97-7.455-8.045-7.455-11.182a7.455 7.455 0 1 1 14.91 0C19.455 12.955 17 16.03 12 21Zm0 0c-2.485-2.485-3.727-4.227-3.727-5.636A3.727 3.727 0 1 1 12 19.364Z" />
              </svg>
              <span>{{ submission.last_seen_address }}</span>
            </div>
          </div>

          <div class="mt-4">
            <div class="mb-1 font-medium text-neutral-900">Description</div>
            <p class="whitespace-pre-line text-neutral-700">{{ submission.description || 'No description provided.' }}</p>
          </div>

          <div class="mt-6 text-sm text-neutral-700 font-medium">📅 Reported on {{ moment(submission.created_at).format('DD/MMMM/yyyy') }} · <span class="font-bold">{{ reportedFromNow }}</span></div>

        </div>
      </div>
      
      <!-- Alerts Block (moved below profile/details, before comments) -->
      <div v-if="submission" class="mt-8">
        <div v-if="isFoundAlive" class="rounded-lg border border-emerald-300 bg-emerald-50 p-4">
          <div class="flex items-center gap-2 font-semibold text-emerald-900">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
              <path fill-rule="evenodd" d="M9 12.75 11.25 15l3.75-5.25a.75.75 0 1 1 1.2.9l-4.5 6.25a.75.75 0 0 1-1.17.08L7.8 13.2a.75.75 0 0 1 1.2-.9Z" clip-rule="evenodd" />
            </svg>
            Great news: Found safe and alive
          </div>
          <p class="mt-1 text-sm text-emerald-900">
            We’re relieved to share that this person has been located and is safe. Our heartfelt thanks to everyone who shared, called, emailed tips, and to SAPS and partners for their support. 💚
          </p>
        </div>
        <div v-else-if="isFoundDead" class="rounded-lg border border-slate-300 bg-slate-50 p-4">
          <div class="flex items-center gap-2 font-semibold text-slate-900">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
              <path d="M11.645 20.91l-.007-.003-.022-.01a15.247 15.247 0 01-.383-.174 25.18 25.18 0 01-4.244-2.532C4.688 16.285 2.25 13.314 2.25 9A6.75 6.75 0 0113.5 4.16 6.75 6.75 0 0121.75 9c0 4.314-2.438 7.285-4.739 9.19a25.175 25.175 0 01-4.244 2.532 15.247 15.247 0 01-.383.174l-.022.01-.007.003a.75.75 0 01-.51 0z" />
            </svg>
            With deep regret: Found deceased
          </div>
          <p class="mt-1 text-sm text-slate-900">
            We share this update with great sadness. Thank you to everyone who assisted, shared information, and supported the search. Our thoughts are with the family and loved ones during this difficult time. 🕊️
          </p>
          <p class="mt-2 text-xs text-slate-700">If you have any information that could assist investigators, please email
            <a :href="`mailto:${contact.email}`" class="underline">{{ contact.email }}</a>.
          </p>
        </div>
        <div v-else class="rounded-lg p-4"
             :class="{
               'border-red-300 bg-red-50': alertTier === 'lt72h',
               'border-orange-300 bg-orange-50': alertTier === 'h72_to_30d',
               'border-amber-300 bg-amber-50': alertTier === 'm1_to_12',
               'border-amber-300 bg-amber-50': alertTier === 'gt12m',
             }"
             :style="{ borderWidth: '1px' }">
          <div class="flex items-center gap-2 font-semibold"
               :class="{
                 'text-red-900': alertTier === 'lt72h',
                 'text-orange-900': alertTier === 'h72_to_30d',
                 'text-amber-900': alertTier === 'm1_to_12' || alertTier === 'gt12m',
               }">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
              <path fill-rule="evenodd" d="M12 2.25c5.385 0 9.75 4.365 9.75 9.75s-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12 6.615 2.25 12 2.25Zm-.53 5.72a.75.75 0 0 1 1.06 0l4.5 4.5a.75.75 0 1 1-1.06 1.06L12.75 10.81V17a.75.75 0 0 1-1.5 0v-6.19l-3.22 3.22a.75.75 0 1 1-1.06-1.06l4.5-4.5Z" clip-rule="evenodd" />
            </svg>
            <template v-if="alertTier === 'lt72h'">Critical: This case was reported within the last 72 hours</template>
            <template v-else-if="alertTier === 'h72_to_30d'">Urgent: This case is 3–30 days old</template>
            <template v-else-if="alertTier === 'm1_to_12'">Important: This case is between 1 and 12 months old</template>
            <template v-else>{{ gt12Label }}</template>
          </div>

          <p class="mt-1 text-sm"
             :class="{
               'text-red-900': alertTier === 'lt72h',
               'text-orange-900': alertTier === 'h72_to_30d',
               'text-amber-900': alertTier === 'm1_to_12' || alertTier === 'gt12m',
             }">
            <template v-if="alertTier === 'lt72h'">
              The first 72 hours are critical. If you saw anything or have information, please contact your local police station (SAPS {{ contact.police }}), email us at
              <a :href="`mailto:${contact.email}`" class="underline">{{ contact.email }}</a>, or call our hotline
              <a :href="`tel:${contact.hotline}`" class="underline">{{ contact.hotline }}</a> immediately.
            </template>
            <template v-else-if="alertTier === 'h72_to_30d'">
              Every tip helps. If you have seen or heard anything in the past days, call SAPS {{ contact.police }}, email a tip at
              <a :href="`mailto:${contact.email}`" class="underline">{{ contact.email }}</a>, or contact our hotline
              <a :href="`tel:${contact.hotline}`" class="underline">{{ contact.hotline }}</a>.
            </template>
            <template v-else-if="alertTier === 'm1_to_12'">
              We continue to appeal to the public for any leads. Please reach out to SAPS {{ contact.police }}, email
              <a :href="`mailto:${contact.email}`" class="underline">{{ contact.email }}</a>, or call our hotline at
              <a :href="`tel:${contact.hotline}`" class="underline">{{ contact.hotline }}</a>.
            </template>
            <template v-else>
              We still urgently need the public’s help. If you have any information, please contact your local police station (SAPS {{ contact.police }}), email us at
              <a :href="`mailto:${contact.email}`" class="underline">{{ contact.email }}</a>, or call our hotline
              <a :href="`tel:${contact.hotline}`" class="underline">{{ contact.hotline }}</a>.
            </template>
          </p>

          <div class="mt-3 flex flex-wrap gap-2">
            <a :href="`tel:${contact.police}`" class="inline-flex items-center gap-2 rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700">
              Call SAPS {{ contact.police }}
            </a>
            <a :href="`mailto:${contact.email}`" class="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-white hover:bg-primary/90">
              Email a tip
            </a>
            <a :href="`tel:${contact.hotline}`" class="inline-flex items-center gap-2 rounded-md bg-blue-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-900/90">
              Call FindSouth
            </a>
            <button v-if="alertTier === 'gt12m' && showAgeProgressionBtn" type="button"
                    :disabled="isGeneratingAge"
                    @click.prevent="handleAgeProgressionClick"
                    class="ml-auto inline-flex items-center gap-2 rounded-md border cursor-pointer border-black bg-black px-3 py-1.5 text-sm font-medium text-white hover:bg-black/90 disabled:opacity-60">
              <svg v-if="isGeneratingAge" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
              </svg>
              <span>{{ isGeneratingAge ? 'Generating preview…' : 'See How They Might Look Like Now With AI' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Map & Street View (after alerts) -->
      <div v-if="submission" class="mt-8">
        <div class="mb-2 font-semibold text-neutral-900">Location preview</div>
        <p class="mb-3 text-sm text-neutral-600">
          The marker shows where they were last seen. Street View on the right is centered on that location.
        </p>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div class="h-72 w-full overflow-hidden rounded-md border" ref="mapEl">
            <div v-if="!apiKey" class="flex h-full items-center justify-center text-sm text-neutral-600 p-4">
              Map preview unavailable (no Google Maps API key configured).
            </div>
          </div>
          <div class="h-72 w-full overflow-hidden rounded-md border" ref="panoEl">
            <div v-if="!apiKey" class="flex h-full items-center justify-center text-sm text-neutral-600 p-4">
              Street View unavailable (no Google Maps API key configured).
            </div>
          </div>
        </div>
      </div>

      <!-- Comments Section -->
      <div class="mx-auto max-w-7xl mt-12" v-if="submission">
        <div class="relative mb-6">
          <div class="h-px w-full bg-gradient-to-r from-transparent via-neutral-300 to-transparent"></div>
          <div class="absolute inset-0 flex items-center ">
            <span class="bg-white  text-neutral-800 text-lg font-medium">Community updates & comments</span>
          </div>
        </div>
        <p class="text-sm text-neutral-700 mb-4">Share any information that could help. Approved comments are shown below; new comments require admin approval.</p>

        <div v-if="comments.length === 0" class="rounded-md border border-neutral-200 bg-white p-4 text-neutral-600">No comments yet.</div>
        <ul v-else class="space-y-3">
          <li v-for="c in comments" :key="c.id" class="rounded-lg border border-neutral-200 bg-white p-4">
            <div class="flex items-start gap-3">
              <img :src="toAbsoluteUrl(c.author_profile_image_url) || `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(c.author_name || 'User')}`" alt="avatar" class="h-9 w-9 rounded-full border border-neutral-200" />
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <div class="text-sm font-medium text-neutral-900">{{ c.author_name || 'Anonymous' }}</div>
                  <div class="text-xs text-neutral-500">{{ moment(c.created_at).fromNow() }}</div>
                </div>
                <p class="mt-1 text-sm text-neutral-800 whitespace-pre-line">{{ c.body }}</p>
                <div v-if="c.image_url" class="mt-2">
                  <img :src="c.image_url" alt="comment image" class="max-h-64 rounded-md border" />
                </div>
              </div>
            </div>
          </li>
        </ul>

        <!-- Add comment form -->
        <div v-if="canComment" class="mt-6 rounded-lg border-1 bg-gray-300 border-gray-100 p-4">
          <div class="text-sm font-medium text-neutral-800 mb-2">Add a comment</div>
          <textarea v-model="newComment" rows="3" class="w-full rounded-md border border-neutral-300 bg-white p-2 text-sm focus:outline-none focus:ring-1 focus:ring-neutral-400" placeholder="Write your comment..."></textarea>
          <div class="mt-2 flex items-center justify-between gap-2">
            <input type="file" accept="image/*" @change="onFileChange" class="text-sm" />
            <button :disabled="sending || !newComment.trim()" @click="submitComment" class="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-white cursor-pointer hover:bg-primary/90 disabled:opacity-50">
              <svg v-if="sending" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
              </svg>
              <span>{{ sending ? 'Submitting…' : 'Submit comment' }}</span>
            </button>
          </div>
          <div class="mt-2 text-xs text-neutral-500">Your comment will be visible after admin approval.</div>
        </div>
        <div v-else class="mt-6 rounded-md border border-gray-50 bg-gray-300 p-4 text-sm text-neutral-700">
          <template v-if="!isAuthenticated">
            Please log in to add a public comment.
            <NuxtLink class="ml-2 text-primary-700 underline" to="/login">Login</NuxtLink>
          </template>
          <template v-else-if="isAdmin">
            Admin accounts cannot post public comments.
          </template>
        </div>
      </div>
    </div>

    <!-- Image Modal -->
    <transition name="fade">
      <div v-if="submission && showImageModal" class="fixed inset-0 z-50 flex items-center justify-center" @click="closeImageModal" aria-modal="true" role="dialog" aria-label="Image preview">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/70"></div>
        <!-- Content -->
        <div class="relative z-10 max-h-[90vh] max-w-[90vw]" @click.stop>
          <img :src="modalImageSrc || currentImage" :alt="submission.full_name" class="max-h-[90vh] max-w-[90vw] object-contain rounded-md shadow-xl" />
          <!-- Close button -->
          <button @click="closeImageModal" class="absolute -top-3 -right-3 rounded-full bg-white/90 p-2 text-neutral-900 shadow hover:bg-white" aria-label="Close image preview">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
              <path fill-rule="evenodd" d="M6.225 4.811a1 1 0 0 1 1.414 0L12 9.172l4.361-4.361a1 1 0 1 1 1.414 1.414L13.414 10.586l4.361 4.361a1 1 0 0 1-1.414 1.414L12 12l-4.361 4.361a1 1 0 0 1-1.414-1.414l4.361-4.361-4.361-4.361a1 1 0 0 1 0-1.414Z" clip-rule="evenodd" />
            </svg>
          </button>
          <!-- Prev/Next controls -->
          <button v-if="!modalImageSrc && canPrev" @click="prevImage" class="absolute left-[-3rem] top-1/2 -translate-y-1/2 rounded-full bg-white/90 p-2 text-neutral-900 shadow hover:bg-white" aria-label="Previous image">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-6 w-6">
              <path d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </button>
          <button v-if="!modalImageSrc && canNext" @click="nextImage" class="absolute right-[-3rem] top-1/2 -translate-y-1/2 rounded-full bg-white/90 p-2 text-neutral-900 shadow hover:bg-white" aria-label="Next image">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-6 w-6">
              <path d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>
