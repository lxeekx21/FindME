<script setup lang="ts">
useHead({ titleTemplate: '%s · FindSouth' })
</script>

<template>
  <div class="min-h-screen bg-neutral-50 text-neutral-900">
    <NavBar />
    <main>
      <slot />
    </main>
  </div>
</template>
