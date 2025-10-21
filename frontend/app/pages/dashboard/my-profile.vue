<script setup lang="ts">
definePageMeta({ layout: 'dashboard', roles: ['user', 'admin'] })

useHead({ title: 'My Profile' })

const { user, accessToken, fetchUser, isLoading } = useAuth()
const { apiBase } = useRuntimeConfig().public

// Tabs
const items = [
  { label: 'Account', slot: 'account' },
  { label: 'Security', slot: 'security' },
]

// Account form state
const accountForm = reactive({
  first_name: '',
  last_name: '',
  dob: '',
  gender: '',
  profile_image_url: '' as string,
  phone: '' as string,
})

const email = computed(() => user.value?.email || '')
const phone = computed(() => user.value?.phone || '')

// Profile image preview
const filePreview = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const triggerFilePicker = () => {
  fileInput.value?.click()
}

const uploadingImage = ref(false)
const uploadError = ref('')

const onFileChange = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  uploadError.value = ''
  if (!file) return
  try {
    // Show immediate local preview
    filePreview.value = URL.createObjectURL(file)
    if (!accessToken.value) return
    uploadingImage.value = true
    const formData = new FormData()
    formData.append('file', file)
    const updated = await $fetch('/auth/me/profile-image', {
      baseURL: apiBase,
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken.value}` },
      body: formData,
    })
    // Update local state with returned user
    accountForm.profile_image_url = (updated as any).profile_image_url || ''
    // Prefer server URL for preview once available
    if ((updated as any).profile_image_url) {
      filePreview.value = (updated as any).profile_image_url
    }
    saveMessage.value = 'Profile image updated.'
  } catch (err: any) {
    uploadError.value = err?.data?.detail || 'Failed to upload image.'
  } finally {
    uploadingImage.value = false
  }
}

watch(
  () => user.value,
  (u) => {
    if (u) {
      accountForm.first_name = u.first_name || ''
      accountForm.last_name = u.last_name || ''
      accountForm.dob = u.dob ? new Date(u.dob as any).toISOString().slice(0, 10) : ''
      // @ts-ignore backend gender is optional string
      accountForm.gender = (u as any).gender || ''
      accountForm.profile_image_url = u.profile_image_url || ''
      accountForm.phone = u.phone || ''
      filePreview.value = u.profile_image_url || null
    }
  },
  { immediate: true }
)

const saving = ref(false)
const saveMessage = ref('')
const saveError = ref('')

const saveAccount = async () => {
  if (!accessToken.value) return
  saving.value = true
  saveMessage.value = ''
  saveError.value = ''
  try {
    const payload: any = {
      first_name: accountForm.first_name || null,
      last_name: accountForm.last_name || null,
      gender: accountForm.gender || null,
      phone: accountForm.phone || null,
    }
    if (accountForm.dob) payload.dob = accountForm.dob
    if (accountForm.profile_image_url) payload.profile_image_url = accountForm.profile_image_url

    const updated = await $fetch('/auth/me', {
      baseURL: apiBase,
      method: 'PATCH',
      headers: { Authorization: `Bearer ${accessToken.value}` },
      body: payload,
    })

    await fetchUser()
    saveMessage.value = 'Profile updated successfully.'
  } catch (err: any) {
    saveError.value = err?.data?.detail || 'Failed to update profile.'
  } finally {
    saving.value = false
  }
}

// Security form
const securityForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const securityLoading = ref(false)
const securityMessage = ref('')
const securityError = ref('')

const changePassword = async () => {
  securityMessage.value = ''
  securityError.value = ''
  if (securityForm.new_password !== securityForm.confirm_password) {
    securityError.value = 'New passwords do not match.'
    return
  }
  if (!accessToken.value) return
  securityLoading.value = true
  try {
    await $fetch('/auth/change-password', {
      baseURL: apiBase,
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken.value}` },
      body: {
        current_password: securityForm.current_password,
        new_password: securityForm.new_password,
      },
    })
    securityMessage.value = 'Password changed successfully.'
    securityForm.current_password = ''
    securityForm.new_password = ''
    securityForm.confirm_password = ''
  } catch (err: any) {
    securityError.value = err?.data?.detail || 'Failed to change password.'
  } finally {
    securityLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <UTabs  :items="items" class="w-full">
      <!-- Account Tab -->
      <template #account>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Left: Profile picture (50%) -->
          <div class="border border-neutral-200 rounded-md p-4 bg-white">
            <h2 class="text-lg font-medium text-neutral-800 mb-4">Profile picture</h2>
            <div class="flex items-center gap-4">
              <img
                :src="filePreview || accountForm.profile_image_url || '/images/logo-black.png'"
                alt="Profile preview"
                title="Click to upload a new picture"
                class="h-40 w-40 md:h-60 md:w-60 rounded-full object-cover border border-neutral-300 cursor-pointer ring-0 hover:ring-2 hover:ring-primary-400"
                @click="triggerFilePicker"
              />
              <div class="flex-1 space-y-3">
                <div>
                  <label class="block text-sm font-medium text-neutral-700 mb-1">Upload new</label>
                  <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" class="sr-only" />
                  <button type="button" @click="triggerFilePicker" class="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-primary text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-400">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-4 w-4"><path d="M12 16.5v-9m0 0l-3 3m3-3l3 3M6.75 19.5h10.5A2.25 2.25 0 0 0 19.5 17.25V9a2.25 2.25 0 0 0-2.25-2.25h-3.318a2.25 2.25 0 0 1-1.59-.659L10.09 4.59a2.25 2.25 0 0 0-1.59-.659H6.75A2.25 2.25 0 0 0 4.5 6.182v11.068A2.25 2.25 0 0 0 6.75 19.5Z"/></svg>
                    <span>Select image</span>
                  </button>
                  <div class="mt-2 flex items-center gap-2">
                    <p class="text-xs text-neutral-500" v-if="!uploadingImage">Click the picture or the button to upload a new image.</p>
                    <p class="text-xs text-neutral-600" v-else>Uploading...</p>
                    <p class="text-xs text-red-600" v-if="uploadError">{{ uploadError }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right: Account details form (50%) -->
          <div class="border border-neutral-200 rounded-md p-4 bg-white">
            <h2 class="text-lg font-medium text-neutral-800 mb-4">Account details</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-neutral-700">First name</label>
                <input v-model="accountForm.first_name" type="text" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700">Last name</label>
                <input v-model="accountForm.last_name" type="text" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700">Date of birth</label>
                <input v-model="accountForm.dob" type="date" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700">Gender</label>
                <select v-model="accountForm.gender" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm">
                  <option value="">Select...</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700">Email</label>
                <input :value="email" type="email" disabled class="mt-1 block w-full rounded-md border border-neutral-200 bg-neutral-100 px-3 py-2 sm:text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700">Phone</label>
                <input v-model="accountForm.phone" type="tel" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" placeholder="e.g. +1 555 123 4567" />
              </div>
            </div>
            <div class="mt-4 flex items-center gap-3">
              <button @click="saveAccount" :disabled="saving" class="inline-flex items-center px-4 py-2 bg-primary text-white rounded-md disabled:opacity-50">
                <span v-if="saving">Saving...</span>
                <span v-else>Save changes</span>
              </button>
              <span v-if="saveMessage" class="text-sm text-green-700">{{ saveMessage }}</span>
              <span v-if="saveError" class="text-sm text-red-700">{{ saveError }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- Security Tab -->
      <template #security>
        <div class="border border-neutral-200 rounded-md p-4 bg-white ">
          <h2 class="text-lg font-medium text-neutral-800 mb-4">Change password</h2>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-neutral-700">Current password</label>
              <input v-model="securityForm.current_password" type="password" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-neutral-700">New password</label>
                <input v-model="securityForm.new_password" type="password" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" />
              </div>
              <div>
                <label class="block text-sm font-medium text-neutral-700">Confirm new password</label>
                <input v-model="securityForm.confirm_password" type="password" class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm" />
              </div>
            </div>
            <div class="flex items-center gap-3">
              <button @click="changePassword" :disabled="securityLoading" class="inline-flex items-center px-4 py-2 bg-primary text-white rounded-md disabled:opacity-50">
                <span v-if="securityLoading">Updating...</span>
                <span v-else>Update password</span>
              </button>
              <span v-if="securityMessage" class="text-sm text-green-700">{{ securityMessage }}</span>
              <span v-if="securityError" class="text-sm text-red-700">{{ securityError }}</span>
            </div>
          </div>
        </div>
      </template>
    </UTabs>
  </div>
</template>
