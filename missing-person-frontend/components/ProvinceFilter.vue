<template>
  <div class="flex gap-3 items-center">
    <label class="font-medium">Province</label>
    <select v-model="selected" @change="onChange" class="p-2 border rounded">
      <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
    </select>
  </div>
</template>

<script setup>
import { ref, defineEmits } from 'vue'
const emit = defineEmits(['change'])
const provinces = [
  'Gauteng',
  'KwaZulu-Natal',
  'Western Cape',
  'Eastern Cape',
  'Limpopo',
  'Mpumalanga',
  'North West',
  'Northern Cape',
  'Free State'
]
const selected = ref(provinces[0])
function onChange() {
  emit('change', selected.value)
}
</script>

<style scoped>
/* keep it simple; Tailwind handles main styling */
</style>
