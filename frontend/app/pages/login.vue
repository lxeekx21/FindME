<script setup lang="ts">
definePageMeta({
  layout: false,
  auth: 'public'
})

useHead({
  title: 'Login - FindSouth',
})

const { login, isLoading, isAuthenticated, initializeAuth } = useAuth()
const router = useRouter()
const route = useRoute()

// If already authenticated, redirect to dashboard
if (process.client) {
  await initializeAuth()
  if (isAuthenticated.value) {
    await router.replace('/dashboard')
  }
}

const form = ref({
  email: '',
  password: ''
})

const error = ref('')

const handleLogin = async () => {
  error.value = ''
  try {
    await login(form.value)
    const nextPath = (route.query.next as string) || '/dashboard'
    await router.push(nextPath)
  } catch (err: any) {
    error.value = err.data?.detail || 'Login failed. Please try again.'
  }
}

const goToRegister = () => {
  router.push('/register')
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
        <h2 class="text-2xl font-semibold">Welcome back</h2>
        <p class="text-white/80">Sign in to your FindSouth account to continue.</p>
      </div>
    </section>

    <!-- Right: login form -->
    <section class="flex items-center justify-center bg-white p-8">
      <div class="w-full max-w-md space-y-6">
        <!-- Logo (mobile only) -->
        <div class="flex justify-center md:hidden">
          <NuxtLink to="/">
            <img src="/images/logo-black.png" alt="FindSouth" class="h-8 w-auto" />
          </NuxtLink>
        </div>

        <div class="space-y-2 text-center">
          <h1 class="text-2xl font-semibold text-neutral-900">Sign in</h1>
          <p class="text-sm text-neutral-600">Enter your credentials to access your account</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div v-if="error" class="rounded-md bg-red-50 p-4">
            <div class="text-sm text-red-700">{{ error }}</div>
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
          <div class="flex justify-end">
            <NuxtLink to="/" class="text-sm text-primary hover:text-primary-600">Forgot your password?</NuxtLink>
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading">Signing in...</span>
            <span v-else>Sign in</span>
          </button>
        </form>

        <div class="text-center">
          <p class="text-sm text-neutral-600">
            Don't have an account?
            <button
              type="button"
              @click="goToRegister"
              class="font-medium cursor-pointer text-primary hover:text-primary-600"
            >
              Sign Up
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
