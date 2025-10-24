<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps({
  transparentTopNav: {
    type: Boolean,
    default: false,
  },
})

const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})
</script>

<template>
  <div v-if="isMounted" class="flex w-full items-center justify-between">
    <div class="flex items-center gap-2">wqeqwe</div>
  </div>
</template>
