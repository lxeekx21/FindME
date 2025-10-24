<script setup lang="ts">
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
  last_seen_place_id?: string | null
  last_seen_lat?: number | null
  last_seen_lng?: number | null
  images?: string[] | null
  created_at: string
}

definePageMeta({ auth: 'public' })

useHead({ title: 'Find missing people across South Africa' })

const router = useRouter()
const { initializeAuth } = useAuth()
const { $api, isApiLoading, lastError } = useApi()
const { public: publicCfg } = useRuntimeConfig()

await initializeAuth()

// Filters
const q = ref('')
const gender = ref<string | null>(null)
const province = ref<string | null>(null)
const statusFilter = ref<string | null>('published')
const PROVINCES = [
  'eastern_cape','free_state','gauteng','kwazulu_natal','limpopo','mpumalanga','north_west','northern_cape','western_cape'
]
const GENDERS = ['male','female']
const STATUSES = ['published','found_alive','found_dead']

// Sort order: 'new' (newest first) or 'oldest'
const sortOrder = ref<'new' | 'oldest'>('new')

// View mode: 'grid' | 'map'
const viewMode = ref<'grid' | 'map'>('grid')

// When switching to map view, default to showing all items so the map has all points
watch(viewMode, (vm) => {
  if (vm === 'map') {
    sizeChoice.value = 'all'
    sortOrder.value = 'new'
  }
})

// Data
const submissions = ref<Submission[]>([])
const page = ref(1)
const sizeChoice = ref<'12' | '24' | '48' | 'all'>('12')
const pageSize = computed(() => sizeChoice.value === 'all' ? Math.max(1, filtered.value.length || 1) : Number(sizeChoice.value))
const total = computed(() => filtered.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const filtered = computed(() => {
  const ql = q.value.trim().toLowerCase()
  // Apply filters first
  let list = submissions.value
    // Only show public cases: published or found
    .filter(s => ['published','found_alive','found_dead'].includes((s.status || '').toLowerCase()))
    .filter(s => !statusFilter.value || (s.status || '').toLowerCase() === statusFilter.value)
    .filter(s => !ql || s.full_name.toLowerCase().includes(ql) || s.title.toLowerCase().includes(ql))
    .filter(s => !gender.value || s.gender === gender.value)
    .filter(s => !province.value || s.province === province.value)

  // Sort by created_at depending on sortOrder
  const sorted = list.slice().sort((a, b) => {
    const at = new Date(a.created_at).getTime()
    const bt = new Date(b.created_at).getTime()
    return sortOrder.value === 'new' ? bt - at : at - bt
  })

  return sorted
})

const paged = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

watch([q, gender, province, statusFilter, sizeChoice, sortOrder], () => { page.value = 1 })

// Map support
const apiKey: string | undefined = publicCfg.googleMapsApiKey
const apiBase: string | undefined = publicCfg.apiBase
const mapId: string | undefined = (publicCfg as any).googleMapsMapId

const hasCoords = computed(() => filtered.value.some(s => typeof s.last_seen_lat === 'number' && typeof s.last_seen_lng === 'number'))
const mapEl = ref<HTMLDivElement | null>(null)
let map: any = null
let markers: any[] = []
let mapsScriptLoaded = false
let clusterer: any = null
let clustererScriptLoaded = false

function toAbsoluteUrl(url?: string | null): string | null {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/')) return `${(apiBase || '').replace(/\/$/, '')}${url}`
  return url
}

function ensureMapsScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (mapsScriptLoaded || (globalThis as any).google?.maps) {
      mapsScriptLoaded = true
      resolve()
      return
    }
    if (!apiKey) {
      reject(new Error('Google Maps API key missing'))
      return
    }
    const cbName = 'initMap' + Math.random().toString(36).slice(2)
    ;(window as any)[cbName] = () => {
      mapsScriptLoaded = true
      resolve()
      delete (window as any)[cbName]
    }
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&libraries=marker&v=weekly&loading=async&callback=${cbName}`
    script.async = true
    script.onerror = () => reject(new Error('Failed to load Google Maps script'))
    document.head.appendChild(script)
  })
}

function ensureClustererScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (clustererScriptLoaded || (window as any).markerClusterer?.MarkerClusterer || (window as any).MarkerClusterer) {
      clustererScriptLoaded = true
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/@googlemaps/markerclusterer/dist/index.min.js'
    script.async = true
    script.onload = () => { clustererScriptLoaded = true; resolve() }
    script.onerror = () => reject(new Error('Failed to load MarkerClusterer script'))
    document.head.appendChild(script)
  })
}

function clearMarkers() {
  if (clusterer && clusterer.clearMarkers) {
    try { clusterer.clearMarkers(); } catch {}
  }
  clusterer = null
  markers.forEach(m => m.setMap && m.setMap(null))
  markers = []
}

function renderMap() {
  if (!mapEl.value) return
  const coords = filtered.value.filter(s => typeof s.last_seen_lat === 'number' && typeof s.last_seen_lng === 'number')
  if (!coords.length) {
    // No coordinates; clear map
    if (map) {
      clearMarkers()
    }
    return
  }
  const SA_CENTER = { lat: -28.4793, lng: 24.6727 }
  const DEFAULT_ZOOM = 6
  const MIN_ZOOM_AFTER_FIT = 6
  const center = SA_CENTER
  if (!map) {
    const mapOptions: any = {
      center,
      zoom: DEFAULT_ZOOM,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true,
    }
    if (mapId) mapOptions.mapId = mapId
    map = new (window as any).google.maps.Map(mapEl.value, mapOptions)
  }
  // Create (or reuse) a single InfoWindow
  if (!(window as any)._sharedInfoWindow) {
    ;(window as any)._sharedInfoWindow = new (window as any).google.maps.InfoWindow()
  }
  const infoWindow = (window as any)._sharedInfoWindow

  clearMarkers()
  const bounds = new (window as any).google.maps.LatLngBounds()

  const g = (window as any).google
  const AdvancedMarker = g?.maps?.marker?.AdvancedMarkerElement

  function markerContentFor(s: Submission) {
    const rawImg = (s.images && s.images.length ? s.images[0] : '') || ''
    const img = toAbsoluteUrl(rawImg) || ''
    const initials = s.full_name?.split(' ').map(p=>p[0]).join('').slice(0,2).toUpperCase()
    const div = document.createElement('div')
    div.className = 'person-marker'
    div.style.width = '48px'
    div.style.height = '48px'
    div.style.borderRadius = '9999px'
    div.style.overflow = 'hidden'
    div.style.boxShadow = '0 2px 6px rgba(0,0,0,0.25)'
    div.style.border = '2px solid #fff'
    div.style.backgroundColor = '#ddd'
    div.style.cursor = 'pointer'
    if (img) {
      const imageEl = document.createElement('img')
      imageEl.src = img
      imageEl.alt = s.full_name
      imageEl.style.width = '100%'
      imageEl.style.height = '100%'
      imageEl.style.objectFit = 'cover'
      div.appendChild(imageEl)
    } else {
      div.style.display = 'flex'
      div.style.alignItems = 'center'
      div.style.justifyContent = 'center'
      div.style.fontSize = '14px'
      div.style.fontWeight = 'bold'
      div.style.color = '#555'
      div.textContent = initials || '•'
    }
    return div
  }

  function buildInfoContent(s: Submission) {
    const safeAddress = s.last_seen_address || 'Location not specified'
    const status = (s.status || '').replace(/_/g,' ')
    const rawImgInfo = (s.images && s.images.length ? s.images[0] : '') || ''
    const img = toAbsoluteUrl(rawImgInfo) || ''
    const html = `
      <div style="display:flex; gap:10px; align-items:flex-start; max-width:300px;">
        <div style="width:64px;height:64px;border-radius:50%;overflow:hidden;background:#eee;flex:0 0 auto;">
          ${img ? `<img src="${img}" alt="${s.full_name}" style="width:100%;height:100%;object-fit:cover;"/>` : ''}
        </div>
        <div style="font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;">
          <div style="font-weight:600; font-size:14px; line-height:1.2; margin-bottom:4px;">${s.full_name}</div>
          <div style="font-size:12px; color:#555; margin-bottom:4px;">Status: ${status}</div>
          <div style="font-size:12px; color:#555;">Last seen: ${safeAddress}</div>
          <div style="margin-top:8px;">
            <a href="/submissions/${s.id}" target="_blank" rel="noopener" style="display:inline-block;padding:6px 10px;border:1px solid #111;border-radius:6px;font-size:12px;text-decoration:none;color:#111;">View</a>
          </div>
        </div>
      </div>`
    return html
  }

  for (const s of coords) {
    const pos = { lat: s.last_seen_lat as number, lng: s.last_seen_lng as number }
    let marker: any
    if (AdvancedMarker) {
      try {
        marker = new AdvancedMarker({
          map,
          position: pos,
          title: s.full_name,
          content: markerContentFor(s),
        })
      } catch (err) {
        // Fallback if Advanced Markers are unavailable without a valid Map ID
        const rawImg = (s.images && s.images.length ? s.images[0] : '') || ''
        const img = toAbsoluteUrl(rawImg) || ''
        const icon = img ? {
          url: img,
          scaledSize: new g.maps.Size(48, 48),
          anchor: new g.maps.Point(24, 24),
        } : undefined
        marker = new g.maps.Marker({ position: pos, map, title: s.full_name, icon })
      }
    } else {
      // Fallback to standard marker with a circular image icon
      const rawImg = (s.images && s.images.length ? s.images[0] : '') || ''
      const img = toAbsoluteUrl(rawImg) || ''
      const icon = img ? {
        url: img,
        scaledSize: new g.maps.Size(48, 48),
        anchor: new g.maps.Point(24, 24),
      } : undefined
      marker = new g.maps.Marker({ position: pos, map, title: s.full_name, icon })
    }

    // Hover to open info window
    g.maps.event.addListener(marker, 'mouseover', () => {
      infoWindow.setContent(buildInfoContent(s))
      infoWindow.open({ map, anchor: marker })
    })

    // Prevent navigation on marker click; instead also open info
    g.maps.event.addListener(marker, 'click', () => {
      infoWindow.setContent(buildInfoContent(s))
      infoWindow.open({ map, anchor: marker })
    })

    markers.push(marker)
    bounds.extend(pos)
  }

  // Initialize marker clustering if library is available
  try {
    const MCNS = (window as any).markerClusterer
    if (MCNS?.MarkerClusterer) {
      clusterer = new MCNS.MarkerClusterer({ map, markers })
    } else if ((window as any).MarkerClusterer) {
      // Legacy global
      clusterer = new (window as any).MarkerClusterer(map, markers)
    }
  } catch {}

  if (coords.length > 1) {
    map.fitBounds(bounds)
    // Ensure we stay reasonably zoomed into South Africa after fitting bounds
    g.maps.event.addListenerOnce(map, 'idle', () => {
      try {
        if (map.getZoom && map.getZoom() < MIN_ZOOM_AFTER_FIT) {
          map.setZoom(MIN_ZOOM_AFTER_FIT)
        }
      } catch {}
    })
  } else {
    map.setCenter(center)
    map.setZoom(10)
  }

  // Close info when clicking on the map background
  ;(window as any).google.maps.event.addListener(map, 'click', () => {
    infoWindow.close()
  })
}

watch([filtered, viewMode], async () => {
  if (viewMode.value !== 'map') return
  try {
    await ensureMapsScript()
    try { await ensureClustererScript() } catch (e) { /* clusterer optional */ }
    // small delay to ensure container is visible
    setTimeout(renderMap, 0)
  } catch (e) {
    console.warn(e)
  }
})

async function fetchSubmissions() {
  try {
    const list = await $api<Submission[]>('/submissions?limit=1000', { method: 'GET', noAuth: true })
    submissions.value = Array.isArray(list) ? list : []
  } catch (e) {
    console.error('Failed to load submissions', e)
  }
}

onMounted(async () => {
  await fetchSubmissions()
})

function viewSubmission(id: number) {
  router.push(`/submissions/${id}`)
}
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="bg-white">
      <div class="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div class="flex flex-col items-start gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 class="text-3xl font-bold tracking-tight text-neutral-900 sm:text-4xl">Help bring them home</h1>
            <p class="mt-2 max-w-2xl text-neutral-600">Browse active cases of missing people. Share, report tips, and help families reunite.</p>
          </div>
          <div class="flex w-full max-w-md items-center gap-2 md:w-auto">
            <input v-model="q" type="text" placeholder="Search by name or case title" class="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-neutral-400 focus:ring-2 focus:ring-neutral-200" />
            <button class="rounded-md border border-neutral-300 px-3 py-2 text-sm hover:bg-neutral-50" @click="q = ''">Clear</button>
          </div>
        </div>

        <!-- Filters bar -->
        <div class="mt-6 flex flex-wrap items-center gap-3">
          <div>
            <label class="mr-2 text-sm text-neutral-600">Status</label>
            <select v-model="statusFilter" class="rounded-md border border-neutral-300 px-2 py-1.5 text-sm">
              <option :value="null">All</option>
              <option v-for="s in STATUSES" :key="s" :value="s">{{ s.charAt(0).toUpperCase() + s.slice(1) }}</option>
            </select>
          </div>
          <div>
            <label class="mr-2 text-sm text-neutral-600">Gender</label>
            <select v-model="gender" class="rounded-md border border-neutral-300 px-2 py-1.5 text-sm">
              <option :value="null">Any</option>
              <option v-for="g in GENDERS" :key="g" :value="g">{{ g.charAt(0).toUpperCase() + g.slice(1) }}</option>
            </select>
          </div>
          <div>
            <label class="mr-2 text-sm text-neutral-600">Province</label>
            <select v-model="province" class="rounded-md border border-neutral-300 px-2 py-1.5 text-sm">
              <option :value="null">Any</option>
              <option v-for="p in PROVINCES" :key="p" :value="p">{{ p.split('_').map(s=>s[0].toUpperCase()+s.slice(1)).join(' ') }}</option>
            </select>
          </div>
          <div>
            <label class="mr-2 text-sm text-neutral-600">Sort by</label>
            <select v-model="sortOrder" class="rounded-md border border-neutral-300 px-2 py-1.5 text-sm disabled:opacity-60" :disabled="viewMode === 'map'">
              <option value="new">Newest</option>
              <option value="oldest">Oldest</option>
            </select>
          </div>
          <div>
            <label class="mr-2 text-sm text-neutral-600">Show</label>
            <select v-model="sizeChoice" class="rounded-md border border-neutral-300 px-2 py-1.5 text-sm disabled:opacity-60" :disabled="viewMode === 'map'">
              <option value="12">12</option>
              <option value="24">24</option>
              <option value="48">48</option>
              <option value="all">All</option>
            </select>
            <span class="ml-1 text-sm text-neutral-500">per page</span>
          </div>
          <!-- View toggle -->
          <div class="ml-auto flex items-center gap-2">
            <div class="inline-flex overflow-hidden rounded-md border border-neutral-300 bg-white">
              <button
                type="button"
                :aria-pressed="viewMode === 'grid'"
                :class="[
                  'appearance-none px-3 py-1.5 text-sm font-medium whitespace-nowrap min-w-16 text-center',
                  viewMode === 'grid' ? 'bg-primary-600 text-white' : 'bg-white text-neutral-700 hover:bg-neutral-50'
                ]"
                @click="viewMode = 'grid'"
              >
                Cards
              </button>
              <button
                type="button"
                :aria-pressed="viewMode === 'map'"
                :class="[
                  'appearance-none px-3 py-1.5 text-sm font-medium whitespace-nowrap min-w-16 text-center border-l border-neutral-300',
                  viewMode === 'map' ? 'bg-primary-600 text-white' : 'bg-white text-neutral-700 hover:bg-neutral-50'
                ]"
                @click="viewMode = 'map'"
              >
                Map
              </button>
            </div>
            <div class="flex items-center gap-2 text-sm text-neutral-600">
              <span>{{ total }} cases</span>
              <span v-if="isApiLoading" class="inline-flex items-center gap-1 text-neutral-500"><span class="h-2 w-2 animate-pulse rounded-full bg-neutral-400"></span> Loading…</span>
              <span v-if="lastError" class="text-red-600">Error loading</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Content -->
    <section class="bg-neutral-50">
      <div class="mx-auto max-w-7xl px-4 pb-12 sm:px-6 lg:px-8">
        <!-- Empty state -->
        <div v-if="!isApiLoading && total === 0" class="rounded-lg border border-neutral-200 bg-white p-10 text-center text-neutral-600">
          <p>No cases found. Try adjusting your filters.</p>
        </div>

        <!-- Grid view -->
        <template v-if="viewMode === 'grid'">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            <MissingPersonCard v-for="s in paged" :key="s.id" :submission="s" @view="viewSubmission" />
          </div>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="mt-8 flex items-center justify-center gap-2">
            <button class="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50" :disabled="page <= 1" @click="page--">Prev</button>
            <span class="text-sm text-neutral-600">Page {{ page }} of {{ totalPages }}</span>
            <button class="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50" :disabled="page >= totalPages" @click="page++">Next</button>
          </div>
        </template>

        <!-- Map view -->
        <template v-else>
          <div class="rounded-lg border border-neutral-200 bg-white p-3">
            <div v-if="!apiKey" class="p-4 text-sm text-amber-700">Google Maps API key is missing; map view is unavailable.</div>
            <div v-else class="relative">
              <div ref="mapEl" class="h-[540px] w-full rounded-md"></div>
              <div v-if="!isApiLoading && !hasCoords" class="absolute inset-0 flex items-center justify-center">
                <div class="rounded-md bg-white/90 px-4 py-2 text-sm text-neutral-700">No locations with coordinates to display.</div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </section>
  </div>
</template>
