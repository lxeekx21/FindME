// composables/useAlerts.js
import { ref } from 'vue'
import { mockAlerts } from '~/data/mockAlerts.js'
import axios from 'axios'

const alerts = ref([])

export function useAlerts() {
  async function loadAlertsByProvince(province) {
    // === MOCK mode (works offline)
    if (process.env.NUXT_PUBLIC_USE_MOCK === 'true' || !useRuntimeConfig().public.apiBase) {
      // simulate network delay
      await new Promise(r => setTimeout(r, 300))
      alerts.value = mockAlerts.filter(a => a.province === province && a.verified)
      return alerts.value
    }

    // === REAL BACKEND mode (swap when backend ready)
    const { public: { apiBase } } = useRuntimeConfig()
    const res = await axios.get(`${apiBase}/alerts`, { params: { province } })
    alerts.value = res.data.filter(a => a.verified)
    return alerts.value
  }

  async function getAlertById(id) {
    if (process.env.NUXT_PUBLIC_USE_MOCK === 'true' || !useRuntimeConfig().public.apiBase) {
      return mockAlerts.find(a => a.id === Number(id))
    }
    const { public: { apiBase } } = useRuntimeConfig()
    const res = await axios.get(`${apiBase}/alerts/${id}`)
    return res.data
  }

  return { alerts, loadAlertsByProvince, getAlertById }
}
