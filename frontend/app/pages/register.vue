<script setup lang="ts">
definePageMeta({
  layout: false,
  auth: 'public'
})

useHead({
  title: 'Register - FindSouth',
})

const { register, isLoading, isAuthenticated, initializeAuth } = useAuth()
const router = useRouter()

// If already authenticated, redirect to dashboard
if (process.client) {
  await initializeAuth()
  if (isAuthenticated.value) {
    await router.replace('/dashboard')
  }
}

const form = ref({
  email: '',
  password: '',
  confirmPassword: '',
  firstName: '',
  lastName: ''
})

const error = ref('')

const handleRegister = async () => {
  error.value = ''
  
  if (form.value.password !== form.value.confirmPassword) {
    error.value = 'Passwords do not match'
    return
  }
  
  if (form.value.password.length < 6) {
    error.value = 'Password must be at least 6 characters long'
    return
  }
  
  try {
    await register({
      email: form.value.email,
      password: form.value.password,
      first_name: form.value.firstName || undefined,
      last_name: form.value.lastName || undefined
    })
    await router.push('/dashboard')
  } catch (err: any) {
    error.value = err.data?.detail || 'Registration failed. Please try again.'
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="grid min-h-screen grid-cols-1 md:grid-cols-2">
    <!-- Left: gradient brand side -->
    <section class="hidden items-center justify-center bg-gradient-to-b from-primary-900 via-primary-800 to-primary-900 p-12 md:flex">
      <div class="max-w-sm space-y-4 text-white">
        <NuxtLink to="/">
          <img src="/images/logo-white.png" alt="FindSouth" class="h-16 w-auto" />
        </NuxtLink>
        <h2 class="text-2xl font-semibold">Join FindSouth</h2>
        <p class="text-white/80">Create your FindSouth account to get started.</p>
      </div>
    </section>

    <!-- Right: register form -->
    <section class="flex items-center justify-center bg-white p-8">
      <div class="w-full max-w-md space-y-6">
        <!-- Logo (mobile only) -->
        <div class="flex justify-center md:hidden">
          <NuxtLink to="/">
            <img src="/images/logo-black.png" alt="FindSouth" class="h-8 w-auto" />
          </NuxtLink>
        </div>

        <div class="space-y-2 text-center">
          <h1 class="text-2xl font-semibold text-neutral-900">Create account</h1>
          <p class="text-sm text-neutral-600">Enter your details to create your account</p>
        </div>

        <form @submit.prevent="handleRegister" class="space-y-4">
          <div v-if="error" class="rounded-md bg-red-50 p-4">
            <div class="text-sm text-red-700">{{ error }}</div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label for="firstName" class="block text-sm font-medium text-neutral-700">First Name</label>
              <input
                id="firstName"
                v-model="form.firstName"
                type="text"
                class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
                placeholder="First name"
              />
            </div>
            <div>
              <label for="lastName" class="block text-sm font-medium text-neutral-700">Last Name</label>
              <input
                id="lastName"
                v-model="form.lastName"
                type="text"
                class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
                placeholder="Last name"
              />
            </div>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-neutral-700">Email</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-neutral-700">Password</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
              placeholder="Enter your password"
            />
          </div>

          <div>
            <label for="confirmPassword" class="block text-sm font-medium text-neutral-700">Confirm Password</label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              required
              class="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
              placeholder="Confirm your password"
            />
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading">Creating account...</span>
            <span v-else>Create account</span>
          </button>
        </form>

        <div class="text-center">
          <p class="text-sm text-neutral-600">
            Already have an account?
            <button
              type="button"
              @click="goToLogin"
              class="font-medium cursor-pointer text-primary hover:text-primary-600"
            >
              Sign in
            </button>
          </p>
        </div>

        <div class="text-center">
          <NuxtLink to="/" class="text-xs text-neutral-500 hover:text-neutral-700 underline underline-offset-2">Back to home</NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>
