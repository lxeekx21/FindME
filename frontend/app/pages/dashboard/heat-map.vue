<script setup lang="ts">
// Admin-only Heat Map page using Google Maps JavaScript API (no Visualization lib)
// Shows heat-like intensity for: Missing (published), Found Alive, Found Deceased

definePageMeta({ layout: 'dashboard', roles: ['admin'] })
useHead({ title: 'Heat Map' })

interface Submission {
  id: number
  status: string
  last_seen_lat?: number | null
  last_seen_lng?: number | null
  last_seen_address?: string | null
  province?: string | null
  created_at: string
}

const { $api, isApiLoading, lastError } = useApi()
const { public: publicCfg } = useRuntimeConfig()
const apiKey: string | undefined = publicCfg.googleMapsApiKey
const mapId: string | undefined = (publicCfg as any).googleMapsMapId

const submissions = ref<Submission[]>([])
const metric = ref<'missing' | 'found_alive' | 'found_dead'>('missing')

// Map refs/state
const mapEl = ref<HTMLDivElement | null>(null)
let map: any = null
let mapsScriptLoaded = false
let scriptPromise: Promise<void> | null = null

// South Africa map defaults
const SA_CENTER = { lat: -28.4793, lng: 24.6727 }
const SA_BOUNDS = { north: -22.0, south: -35.0, east: 33.0, west: 16.0 }
const DEFAULT_ZOOM = 14

// Heat-like overlays (google.maps.Circle instances)
let heatCircles: any[] = []

const hasAnyCoords = computed(() => submissions.value.some(s => typeof s.last_seen_lat === 'number' && typeof s.last_seen_lng === 'number'))

async function fetchSubmissions() {
  try {
    const list = await $api<Submission[]>('/submissions', { method: 'GET', noAuth: true })
    submissions.value = Array.isArray(list) ? list : []
  } catch (e) {
    // handled by lastError in composable
  }
}

function ensureMapsScript(): Promise<void> {
  if (mapsScriptLoaded || (globalThis as any).google?.maps) {
    mapsScriptLoaded = true
    return Promise.resolve()
  }
  if (scriptPromise) return scriptPromise
  if (!apiKey) return Promise.reject(new Error('Google Maps API key missing'))

  scriptPromise = new Promise((resolve, reject) => {
    const cbName = 'initMapBase' + Math.random().toString(36).slice(2)
    ;(window as any)[cbName] = () => {
      mapsScriptLoaded = true
      resolve()
      delete (window as any)[cbName]
    }
    const params = new URLSearchParams({
      key: apiKey,
      v: 'weekly',
      loading: 'async',
      callback: cbName,
    })
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?${params.toString()}`
    script.async = true
    script.onerror = () => reject(new Error('Failed to load Google Maps script'))
    document.head.appendChild(script)
  })
  return scriptPromise
}

function pointsForMetric(): Array<{ lat: number; lng: number }> {
  const statusMap: Record<'missing' | 'found_alive' | 'found_dead', string> = {
    missing: 'published',
    found_alive: 'found_alive',
    found_dead: 'found_dead',
  }
  const want = statusMap[metric.value]
  const pts: Array<{ lat: number; lng: number }> = []
  for (const s of submissions.value) {
    const st = (s.status || '').toLowerCase()
    if (st !== want) continue
    if (typeof s.last_seen_lat !== 'number' || typeof s.last_seen_lng !== 'number') continue
    pts.push({ lat: s.last_seen_lat, lng: s.last_seen_lng })
  }
  return pts
}

function clearHeatOverlays() {
  if (!heatCircles.length) return
  for (const c of heatCircles) {
    try { c.setMap(null) } catch {}
  }
  heatCircles = []
}

function colorForMetric(): string {
  // teal for missing, green for alive, red for deceased
  if (metric.value === 'missing') return '#0d9488'
  if (metric.value === 'found_alive') return '#22c55e'
  return '#ef4444'
}

function renderHeatmap() {
  if (!mapEl.value) return
  const g = (window as any).google
  const pts = pointsForMetric()

  // Initialize map if needed
  if (!map) {
    // Simple, clean basemap style: hide all labels, POIs, roads, transit; allow only country label
    const SIMPLE_NEAT_STYLE: any[] = [
      { featureType: 'road', elementType: 'all', stylers: [{ visibility: 'off' }] },
      { featureType: 'transit', elementType: 'all', stylers: [{ visibility: 'off' }] },
      { featureType: 'poi', elementType: 'all', stylers: [{ visibility: 'off' }] },
      { featureType: 'administrative.locality', elementType: 'all', stylers: [{ visibility: 'off' }] },
      { featureType: 'administrative.province', elementType: 'all', stylers: [{ visibility: 'off' }] },
      { featureType: 'administrative.country', elementType: 'labels.text.fill', stylers: [{ visibility: 'on' }, { color: '#303030' }] },
      { featureType: 'administrative.country', elementType: 'labels.text.stroke', stylers: [{ visibility: 'off' }] },
      { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#dfe9f3' }] },
      { featureType: 'landscape', elementType: 'geometry', stylers: [{ color: '#f3f4f6' }] },
    ]

    const options: any = {
      center: SA_CENTER,
      zoom: DEFAULT_ZOOM,
      mapTypeId: 'roadmap',
      styles: SIMPLE_NEAT_STYLE,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true,
      restriction: { latLngBounds: SA_BOUNDS, strictBounds: false },
    }
    // Intentionally do NOT set mapId here so that custom styles always apply on the neat heat map
    map = new g.maps.Map(mapEl.value, options)
  }

  // Clear previous overlays
  clearHeatOverlays()


  // Create semi-transparent circles for each point to simulate heat
  const fillColor = colorForMetric()
  const baseOpacity = 0.25
  const radiusMeters = 20000 // 20km blob; looks reasonable at SA zoom; overlaps will intensify

  const bounds = new g.maps.LatLngBounds()

  for (const p of pts) {
    const circle = new g.maps.Circle({
      map,
      center: p,
      radius: radiusMeters,
      strokeOpacity: 0,
      strokeWeight: 0,
      fillColor,
      fillOpacity: baseOpacity,
    })
    heatCircles.push(circle)
    bounds.extend(p)
  }

  // Fit map to entire South Africa, regardless of point spread
  // This ensures the full country is always visible.
  map.fitBounds(SA_BOUNDS, 32) // add small padding so the edges are not clipped
  const MIN_ZOOM_AFTER_FIT = 5
  const MAX_ZOOM_AFTER_FIT = DEFAULT_ZOOM // avoid zooming in too close; keep a national view
  g.maps.event.addListenerOnce(map, 'idle', () => {
    try {
      if (map.getZoom) {
        let z = map.getZoom()
        if (z < MIN_ZOOM_AFTER_FIT) z = MIN_ZOOM_AFTER_FIT
        if (z > MAX_ZOOM_AFTER_FIT) z = MAX_ZOOM_AFTER_FIT
        map.setZoom(z)
        // recentre to ensure the full country is framed regardless of container aspect ratio
        map.setCenter(SA_CENTER)
      }
    } catch {}
  })
}

watch([metric, submissions], async () => {
  if (!apiKey) return
  try {
    await ensureMapsScript()
    // slight delay to ensure container is visible
    setTimeout(renderHeatmap, 0)
  } catch (e) {
    console.warn(e)
  }
})

onMounted(async () => {
  await fetchSubmissions()
  if (apiKey) {
    try {
      await ensureMapsScript()
      setTimeout(renderHeatmap, 0)
    } catch (e) {
      console.warn(e)
    }
  }
})
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-neutral-900">Heat Map</h1>
        <p class="text-sm text-neutral-600">Visualize concentration by outcome: Missing, Found Alive, Found Deceased.</p>
      </div>
      <div class="inline-flex overflow-hidden rounded-md border border-neutral-300 bg-white">
        <button
          type="button"
          :aria-pressed="metric === 'missing'"
          :class="['appearance-none px-3 py-1.5 text-sm font-medium whitespace-nowrap min-w-20 text-center', metric === 'missing' ? 'bg-primary-600 text-white' : 'bg-white text-neutral-700 hover:bg-neutral-50']"
          @click="metric = 'missing'"
        >Missing</button>
        <button
          type="button"
          :aria-pressed="metric === 'found_alive'"
          :class="['appearance-none px-3 py-1.5 text-sm font-medium whitespace-nowrap min-w-20 text-center border-l border-neutral-300', metric === 'found_alive' ? 'bg-primary-600 text-white' : 'bg-white text-neutral-700 hover:bg-neutral-50']"
          @click="metric = 'found_alive'"
        >Found Alive</button>
        <button
          type="button"
          :aria-pressed="metric === 'found_dead'"
          :class="['appearance-none px-3 py-1.5 text-sm font-medium whitespace-nowrap min-w-20 text-center border-l border-neutral-300', metric === 'found_dead' ? 'bg-primary-600 text-white' : 'bg-white text-neutral-700 hover:bg-neutral-50']"
          @click="metric = 'found_dead'"
        >Found Deceased</button>
      </div>
    </div>

    <div class="rounded-lg border border-neutral-200 bg-white p-3">
      <div class="relative">
        <div class="relative h-[600px] w-full rounded-md overflow-hidden">
          <div v-if="!apiKey" class="p-4 text-sm text-amber-700">Google Maps API key is missing; heat map is unavailable.</div>
          <div v-else ref="mapEl" class="h-[600px] w-full"></div>

          <!-- Empty state overlay -->
          <div v-if="apiKey && !isApiLoading && !hasAnyCoords" class="absolute inset-0 flex items-center justify-center">
            <div class="rounded-md bg-white/90 px-4 py-2 text-sm text-neutral-700">No locations with coordinates to display.</div>
          </div>

          <!-- Legend -->
          <div class="absolute bottom-3 left-3 rounded-md bg-white/90 px-3 py-2 text-xs text-neutral-700 shadow">
            <div class="font-medium mb-1">Legend</div>
            <div v-if="metric === 'missing'">Teal intensity shows concentration of active missing cases (status: published).</div>
            <div v-else-if="metric === 'found_alive'">Green intensity shows concentration of cases found alive.</div>
            <div v-else>Red intensity shows concentration of cases found deceased.</div>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-3 text-sm text-neutral-600 flex items-center gap-3">
      <span>Total records: {{ submissions.length }}</span>
      <span v-if="isApiLoading" class="inline-flex items-center gap-1 text-neutral-500"><span class="h-2 w-2 animate-pulse rounded-full bg-neutral-400"></span> Loading…</span>
      <span v-if="lastError" class="text-red-600">Error loading data</span>
    </div>
  </div>
</template>
