<template>
  <div class="mt-4">
    <h3 class="font-semibold mb-2">
      {{ props.alertId ? 'Comments for this Alert' : 'Community Comments' }}
    </h3>

    <div v-if="comments.length" v-for="c in comments" :key="c.id" class="mb-3 p-3 bg-gray-50 rounded">
      <div class="text-sm text-gray-700">{{ c.text }}</div>
      <div class="text-xs text-gray-400 mt-2">— {{ c.author }} • {{ c.when }}</div>
    </div>
    <div v-else class="text-gray-500 text-sm mb-4">No comments yet.</div>

    <form @submit.prevent="submit" class="mt-4 flex flex-col gap-2">
      <textarea
        v-model="newComment"
        rows="3"
        class="p-2 border rounded"
        placeholder="Add a helpful comment..."
      ></textarea>
      <div class="flex gap-3">
        <input
          v-model="author"
          placeholder="Your name"
          class="p-2 border rounded flex-1"
        />
        <button
          class="bg-blue-600 text-white px-4 py-2 rounded"
          :disabled="!newComment"
        >
          Post
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  alertId: {
    type: [String, Number],
    default: null
  }
})

//  global + per-alert comment stores
const globalComments = ref([
  { id: 1, author: 'ConcernedCitizen', text: 'Hoping for everyone’s safe return.', when: '2025-10-14' }
])
const commentsByAlert = ref({})

// reactive computed source
const comments = computed(() => {
  if (props.alertId) {
    if (!commentsByAlert.value[props.alertId]) {
      commentsByAlert.value[props.alertId] = []
    }
    return commentsByAlert.value[props.alertId]
  }
  return globalComments.value
})

const newComment = ref('')
const author = ref('')

function submit() {
  const comment = {
    id: Date.now(),
    author: author.value || 'Anonymous',
    text: newComment.value,
    when: new Date().toISOString().slice(0, 10)
  }

  if (props.alertId) {
    commentsByAlert.value[props.alertId].unshift(comment)
  } else {
    globalComments.value.unshift(comment)
  }

  newComment.value = ''
  author.value = ''
}
</script>
