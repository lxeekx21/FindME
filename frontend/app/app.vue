<script setup lang="ts">
import { en } from '@nuxt/ui/locale'
</script>

<template>
  <UApp :locale="en">
    <NuxtLayout>
      <NuxtPage />
      <ClientOnly>
        <UToaster :duration="7500" />
      </ClientOnly>
    </NuxtLayout>
  </UApp>
</template>
