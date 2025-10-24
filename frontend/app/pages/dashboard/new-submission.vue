<script setup lang="ts">
definePageMeta({ layout: 'dashboard', roles: ['user', 'admin'] })
useHead({ title: 'New Submission' })

const { accessToken } = useAuth()
const { apiBase } = useRuntimeConfig().public
const router = useRouter()

// Form state
const form = reactive({
  title: '' as string,
  full_name: '',
  dob: '' as string,
  gender: '' as string,
  race: '' as string,
  height: '' as string | number,
  weight: '' as string | number,
  province: '' as string,
  description: '' as string,
  last_seen_address: '' as string,
  last_seen_place_id: '' as string,
  last_seen_lat: '' as string | number,
  last_seen_lng: '' as string | number,
})

// Images
const files = ref<File[]>([])
const previews = ref<string[]>([])

const onFilesChange = (e: Event) => {
  const input = e.target as HTMLInputElement
  const selected = Array.from(input.files || [])
  files.value = selected
  previews.value.forEach(url => URL.revokeObjectURL(url))
  previews.value = selected.map(f => URL.createObjectURL(f))
}

const pickInput = ref<HTMLInputElement | null>(null)
const triggerPick = () => pickInput.value?.click()

// Address autocomplete using Places API (New) via HTTP; see AddressAutoComplete component
const onPlaceChanged = (payload: { formattedAddress: string; coordinates?: { lat: number; lng: number } | null; place: any }) => {
  form.last_seen_address = payload.formattedAddress || ''
  // Prefer explicit id if provided
  // Places API (New) returns id, not legacy place_id
  const pid = (payload.place && (payload.place.placeId || payload.place.id)) || ''
  form.last_seen_place_id = pid
  if (payload.coordinates) {
    form.last_seen_lat = payload.coordinates.lat
    form.last_seen_lng = payload.coordinates.lng
  }
}

// Basic validation
const error = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  if (!form.full_name.trim()) {
    error.value = 'Full name is required.'
    return
  }
  if (!form.title.trim()) {
    error.value = 'Title is required.'
    return
  }
  if (files.value.length < 3) {
    error.value = 'Please select at least 3 images.'
    return
  }
  if (!accessToken.value) {
    error.value = 'You must be logged in.'
    return
  }

  const fd = new FormData()
  fd.append('title', form.title)
  fd.append('full_name', form.full_name)
  if (String(form.dob || '').trim()) fd.append('dob', String(form.dob))
  if (form.gender) fd.append('gender', form.gender)
  if (form.race) fd.append('race', form.race)
  if (String(form.height || '').trim()) fd.append('height', String(form.height))
  if (String(form.weight || '').trim()) fd.append('weight', String(form.weight))
  if (form.province) fd.append('province', form.province)
  if (form.description) fd.append('description', form.description)
  if (form.last_seen_address) fd.append('last_seen_address', form.last_seen_address)
  if (form.last_seen_place_id) fd.append('last_seen_place_id', form.last_seen_place_id)
  if (String(form.last_seen_lat || '').trim()) fd.append('last_seen_lat', String(form.last_seen_lat))
  if (String(form.last_seen_lng || '').trim()) fd.append('last_seen_lng', String(form.last_seen_lng))
  files.value.forEach(f => fd.append('images', f))

  loading.value = true
  try {
    await $fetch('/submissions/', {
      baseURL: apiBase,
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken.value}` },
      body: fd,
    })
    // Go to My Submissions for users, or Submissions for admins
    const roleDefault = '/dashboard/my-submissions'
    await router.push(roleDefault)
  } catch (err: any) {
    error.value = err?.data?.detail || 'Failed to submit. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class=" mx-auto ">
    <div v-if="error" class="rounded-md bg-red-50 p-3 text-red-700">{{ error }}</div>

    <form class="bg-white border border-neutral-200 rounded-md p-4 space-y-4" @submit.prevent="submit">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-neutral-700">Full name</label>
          <input v-model="form.full_name" type="text" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" placeholder="Missing person's full name" />
        </div>
        <div>
          <label class="block text-sm font-medium text-neutral-700">Date of birth</label>
          <input v-model="form.dob" type="date" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" placeholder="DOB (optional)" />
        </div>
        <div>
          <label class="block text-sm font-medium text-neutral-700">Gender</label>
          <select v-model="form.gender" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm">
            <option value="">Select...</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-neutral-700">Race</label>
          <select v-model="form.race" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm">
            <option value="">Select...</option>
            <option value="black_african">Black African</option>
            <option value="coloured">Coloured</option>
            <option value="white">White</option>
            <option value="asian_or_indian">Asian or Indian</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-neutral-700">Province</label>
          <select v-model="form.province" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm">
            <option value="">Select...</option>
            <option value="eastern_cape">Eastern Cape</option>
            <option value="free_state">Free State</option>
            <option value="gauteng">Gauteng</option>
            <option value="kwazulu_natal">KwaZulu-Natal</option>
            <option value="limpopo">Limpopo</option>
            <option value="mpumalanga">Mpumalanga</option>
            <option value="north_west">North West</option>
            <option value="northern_cape">Northern Cape</option>
            <option value="western_cape">Western Cape</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-neutral-700">Height (cm)</label>
          <input v-model="form.height" type="number" min="0" step="any" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" placeholder="Optional" />
        </div>
        <div>
          <label class="block text-sm font-medium text-neutral-700">Weight (kg)</label>
          <input v-model="form.weight" type="number" min="0" step="any" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" placeholder="Optional" />
        </div>
        <div>
          <label class="block text-sm font-medium text-neutral-700">Last seen address</label>
          <UiAddressAutoComplete
            v-model="form.last_seen_address"
            placeholder="Search address"
            @placeChanged="onPlaceChanged"
            :enforceSelection="true"
            :country="['ZA']"
          />
        </div>
        <div class="hidden" aria-hidden="true">
          <input v-model="form.last_seen_lat" type="hidden" />
        </div>
        <div class="hidden" aria-hidden="true">
          <input v-model="form.last_seen_lng" type="hidden" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-neutral-700">Title</label>
        <input v-model="form.title" type="text" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" placeholder="Short headline, e.g., Missing: John Doe (Gauteng)" />
      </div>

      <div>
        <label class="block text-sm font-medium text-neutral-700">Description</label>
        <textarea v-model="form.description" rows="4" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" placeholder="Provide any details that may help identify them"></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-neutral-700">Photos (min 3)</label>
        <input ref="pickInput" type="file" accept="image/*" multiple class="sr-only" @change="onFilesChange" />
        <div class="mt-1 flex items-center gap-3">
          <button type="button" @click="triggerPick" class="inline-flex items-center px-3 py-2 rounded-md bg-primary text-white hover:bg-primary-700">Choose images</button>
          <span class="text-sm text-neutral-600" v-if="!files.length">No files selected</span>
          <span class="text-sm text-neutral-700" v-else>{{ files.length }} file(s) selected</span>
        </div>
        <div class="mt-3 grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
          <img v-for="(src, i) in previews" :key="i" :src="src" class="h-20 w-20 object-cover rounded border" />
        </div>
      </div>

      <div class="pt-2 flex items-center gap-3">
        <button type="submit" :disabled="loading" class="inline-flex items-center px-4 py-2 bg-primary text-white rounded-md disabled:opacity-50">{{ loading ? 'Submitting...' : 'Submit' }}</button>
        <span class="text-sm text-neutral-600">Status will be set to <strong>pending</strong> until reviewed.</span>
      </div>
    </form>
  </div>
</template>
