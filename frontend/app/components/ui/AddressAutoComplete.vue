<script setup lang="ts">
import { onMounted, ref, watch, onBeforeUnmount, nextTick } from 'vue'

// Minimal, framework-free Places API (New) address autocomplete
// Emits:
// - update:modelValue: string (formatted address)
// - placeChanged: { place, formattedAddress, coordinates?, components }

type Suggestion = { id: string; text: string; placeId?: string }

type PlaceDetails = {
  formattedAddress?: string
  location?: { latitude?: number; longitude?: number }
  addressComponents?: Array<{ longText?: string; shortText?: string; types?: string[] }>
  id?: string
  placeId?: string
  [k: string]: any
}

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Search address…' },
  country: { type: [String, Array] as any, default: 'ZA' },
  disabled: { type: Boolean, default: false },
  name: { type: String, default: 'address' },
  id: { type: String, default: undefined },
  autofocus: { type: Boolean, default: false },
  enforceSelection: { type: Boolean, default: false },
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (
    e: 'placeChanged',
    payload: {
      place: any
      formattedAddress: string
      coordinates?: { lat: number; lng: number } | null
      components: Record<string, string>
    }
  ): void
}>()

const inputEl = ref<HTMLInputElement | null>(null)
const localValue = ref<string>(props.modelValue || '')
const suggestions = ref<Suggestion[]>([])
const open = ref(false)
const highlighted = ref(-1)
let debounceTimer: any = null
let blurTimer: any = null

const { public: publicCfg } = useRuntimeConfig()
const apiKey: string | undefined = publicCfg.googleMapsApiKey

const sessionToken = ref<string | null>(null)
function ensureSessionToken() {
  if (!sessionToken.value) sessionToken.value = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2)
}
function clearSessionToken() {
  sessionToken.value = null
}

function parseAddressComponents(details: PlaceDetails): Record<string, string> {
  const out: Record<string, string> = {}
  const comps = details.addressComponents || []
  for (const c of comps) {
    const type = c.types && c.types.length ? c.types[0] : undefined
    if (!type) continue
    if (c.longText) out[type] = c.longText
    if (c.shortText) out[`${type}_short`] = c.shortText
  }
  return out
}

async function fetchAutocomplete(query: string) {
  if (!apiKey) {
    suggestions.value = []
    open.value = false
    return
  }
  if (!query || query.length < 3) {
    suggestions.value = []
    open.value = false
    return
  }
  ensureSessionToken()
  try {
    const toArr = (v: any) => (Array.isArray(v) ? v : v ? [v] : [])
    const regionCodes = toArr(props.country).filter((c: any) => typeof c === 'string' && c.length === 2)

    const body: any = {
      input: query,
      sessionToken: sessionToken.value,
      languageCode: 'en',
    }
    if (regionCodes.length) body.includedRegionCodes = regionCodes

    const res = await fetch('https://places.googleapis.com/v1/places:autocomplete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': apiKey,
      },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`Autocomplete failed: ${res.status}`)
    const data = await res.json()
    const list: Suggestion[] = (data.suggestions || []).map((s: any, idx: number) => {
      const t = s.placePrediction?.text?.text || s.queryPrediction?.text?.text || ''
      const pid = s.placePrediction?.placeId
      return { id: `${pid || 'q'}-${idx}`, text: t, placeId: pid }
    })
    suggestions.value = list
    open.value = list.length > 0
    highlighted.value = list.length ? 0 : -1
  } catch (e) {
    suggestions.value = []
    open.value = false
  }
}

async function fetchPlaceDetails(placeId: string): Promise<PlaceDetails | null> {
  if (!apiKey) return null
  const url = `https://places.googleapis.com/v1/places/${encodeURIComponent(placeId)}`
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      'X-Goog-Api-Key': apiKey,
      // Field mask required by Places API (New)
      'X-Goog-FieldMask': 'formattedAddress,location,addressComponents,id',
    },
  })
  if (!res.ok) return null
  const data = (await res.json()) as PlaceDetails
  return data
}

function onInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  try { localValue.value = val } catch {}
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => fetchAutocomplete(val), 250)
}

function onKeydown(e: KeyboardEvent) {
  if (!open.value || !suggestions.value.length) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    highlighted.value = (highlighted.value + 1) % suggestions.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    highlighted.value = (highlighted.value - 1 + suggestions.value.length) % suggestions.value.length
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (highlighted.value >= 0) selectSuggestion(suggestions.value[highlighted.value])
  } else if (e.key === 'Escape') {
    open.value = false
    if (props.enforceSelection) {
      const committed = props.modelValue || ''
      if ((localValue.value || '') !== committed) {
        if (inputEl.value) inputEl.value.value = committed
        try { localValue.value = committed } catch {}
      }
    }
  }
}

async function selectSuggestion(s: Suggestion) {
  const typedBefore = inputEl.value ? inputEl.value.value : localValue.value
  open.value = false
  if (inputEl.value) inputEl.value.value = s.text
  try { localValue.value = s.text } catch {}

  let formatted = s.text
  let coords: { lat: number; lng: number } | null = null
  let components: Record<string, string> = {}
  let place: any = { text: s.text, placeId: s.placeId }

  if (s.placeId) {
    const details = await fetchPlaceDetails(s.placeId)
    if (details) {
      place = details
      formatted = details.formattedAddress || s.text
      const loc = details.location
      if (loc && typeof loc.latitude === 'number' && typeof loc.longitude === 'number') {
        coords = { lat: loc.latitude!, lng: loc.longitude! }
      }
      components = parseAddressComponents(details)

      // Preserve house number if user typed it and API omits it
      const typed = (typedBefore || '').trim()
      const houseMatch = typed.match(/^\d+[A-Za-z\-\/]?/)
      const hasStreetNumberComponent = Boolean(components['street_number'])
      const looksLikeRoute = Boolean(components['route'])
      const formattedHasNumber = /\b\d+[A-Za-z\-\/]?\b/.test(formatted)
      if (!hasStreetNumberComponent && looksLikeRoute && houseMatch && !formattedHasNumber) {
        formatted = `${houseMatch[0]} ${formatted}`
        components['street_number'] = houseMatch[0]
      }
    }
  }

  if (inputEl.value) inputEl.value.value = formatted
  try { localValue.value = formatted } catch {}
  emit('update:modelValue', formatted)
  emit('placeChanged', { place, formattedAddress: formatted, coordinates: coords, components })
  clearSessionToken()
}

function onFocus() {
  if (suggestions.value.length) open.value = true
}

function onBlur() {
  blurTimer = setTimeout(() => {
    open.value = false
    if (props.enforceSelection) {
      const committed = props.modelValue || ''
      if ((localValue.value || '') !== committed) {
        if (inputEl.value) inputEl.value.value = committed
        try { localValue.value = committed } catch {}
      }
    }
  }, 150)
}

function clearValue() {
  if (debounceTimer) clearTimeout(debounceTimer)
  suggestions.value = []
  open.value = false
  try { localValue.value = '' } catch {}
  if (inputEl.value) {
    inputEl.value.value = ''
    inputEl.value.focus()
  }
  emit('update:modelValue', '')
  clearSessionToken()
}

onMounted(async () => {
  await nextTick()
  const initial = props.modelValue || ''
  if (inputEl.value) inputEl.value.value = initial
  try { localValue.value = initial } catch {}
})

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (blurTimer) clearTimeout(blurTimer)
})

watch(
  () => props.modelValue,
  (val) => {
    const v = val || ''
    if (inputEl.value && inputEl.value.value !== v) {
      inputEl.value.value = v
    }
    try { if (localValue.value !== v) localValue.value = v } catch {}
  }
)
</script>

<template>
  <div class="relative w-full">
    <input
      ref="inputEl"
      :id="id"
      :name="name"
      type="text"
      class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm bg-white"
      :placeholder="placeholder"
      :autofocus="autofocus"
      :disabled="disabled"
      :value="localValue"
      @input="onInput"
      @keydown="onKeydown"
      @focus="onFocus"
      @blur="onBlur"
      autocomplete="off"
      spellcheck="false"
    />

    <button
      v-if="(localValue?.length || 0) > 0"
      type="button"
      class="absolute top-1/2 right-2 -translate-y-1/2 inline-flex h-6 w-6 items-center justify-center rounded hover:bg-neutral-100"
      @mousedown.prevent
      @click="clearValue"
      aria-label="Clear"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-4 w-4 text-neutral-500"><path fill-rule="evenodd" d="M6.225 4.811a.75.75 0 011.06 0L12 9.525l4.715-4.714a.75.75 0 111.06 1.06L13.06 10.586l4.715 4.714a.75.75 0 11-1.06 1.06L12 11.646l-4.715 4.714a.75.75 0 01-1.06-1.06l4.714-4.715-4.714-4.714a.75.75 0 010-1.06z" clip-rule="evenodd"/></svg>
    </button>

    <div v-if="open && suggestions.length" class="absolute z-50 mt-1 w-full rounded-md border border-neutral-200 bg-white shadow-lg">
      <ul class="max-h-60 overflow-auto py-1">
        <li
          v-for="(s, idx) in suggestions"
          :key="s.id"
          @mousedown.prevent="selectSuggestion(s)"
          class="cursor-pointer px-3 py-2 text-sm text-neutral-800 hover:bg-neutral-100"
          :class="{ 'bg-neutral-100': idx === highlighted }"
        >
          {{ s.text }}
        </li>
      </ul>
    </div>

    <p v-if="!apiKey" class="mt-1 text-xs text-amber-700">Google Maps API key missing: address autocomplete disabled.</p>
  </div>
</template>
