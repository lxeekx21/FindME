<script setup lang="ts">
definePageMeta({ layout: 'dashboard', roles: ['admin'] })
useHead({ title: 'Analytics & Reports', script: [{ src: 'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js', defer: true }] })

const { accessToken } = useAuth()
const { apiBase } = useRuntimeConfig().public

  interface SummaryDTO {
  total_submissions: number
  status_counts?: Record<string, number>
  province_counts?: Record<string, number>
  gender_counts?: Record<string, number>
  race_counts?: Record<string, number>
  monthly_new?: { month: string; count: number }[]
  public_counts?: { public: number; non_public: number }
  found_rate?: number
  found_alive_count?: number
  found_dead_count?: number
  avg_images_per_submission?: number
  users_total?: number
  admins_total?: number
  active_users?: number
  inactive_users?: number
  top_submitters?: { user_id: number; count: number }[]
 }

const loading = ref(false)
const error = ref('')
const data = ref<SummaryDTO | null>(null)

async function fetchSummary() {
  if (!accessToken.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await $fetch<SummaryDTO>('/submissions/summary', {
      baseURL: apiBase,
      headers: { Authorization: `Bearer ${accessToken.value}` },
    })
    data.value = res
    await nextTick()
    await waitForEcharts()
    initCharts()
  } catch (e: any) {
    error.value = e?.data?.detail || 'Failed to load analytics.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchSummary)
watch(accessToken, (v) => { if (v) fetchSummary() })

// ECharts helpers
let resizeObserver: (() => void) | null = null
let echartsReadyPromise: Promise<void> | null = null
function waitForEcharts(timeoutMs = 7000): Promise<void> {
  if (typeof window !== 'undefined' && (window as any).echarts) return Promise.resolve()
  if (echartsReadyPromise) return echartsReadyPromise
  echartsReadyPromise = new Promise<void>((resolve, reject) => {
    const started = Date.now()
    const check = () => {
      if ((window as any).echarts) {
        resolve()
        return
      }
      if (Date.now() - started > timeoutMs) {
        reject(new Error('ECharts failed to load'))
        return
      }
      setTimeout(check, 100)
    }
    // If script tag exists it will eventually set window.echarts; otherwise rely on useHead injected tag
    check()
  })
  return echartsReadyPromise
}
function initCharts() {
  if (typeof window === 'undefined' || !window || !(window as any).echarts) return
  const echarts = (window as any).echarts

  const charts: { el: string; option: any }[] = []

  const statusCounts = data.value?.status_counts || {}
  charts.push({
    el: 'statusChart',
    option: {
      tooltip: { trigger: 'item' },
      legend: { top: 'bottom' },
      series: [{
        name: 'Status',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        data: Object.entries(statusCounts).map(([name, value]) => ({ name, value })),
      }],
    },
  })

  const monthly = (data.value?.monthly_new || []).map(m => ({ ...m }))
  charts.push({
    el: 'monthlyChart',
    option: {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: monthly.map(m => m.month) },
      yAxis: { type: 'value' },
      series: [{ data: monthly.map(m => m.count), type: 'line', smooth: true, areaStyle: {} }],
    },
  })

  const provinceCounts = data.value?.province_counts || {}
  charts.push({
    el: 'provinceChart',
    option: {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: Object.keys(provinceCounts).map(k => k.split('_').map(s=>s[0].toUpperCase()+s.slice(1)).join(' ')) },
      yAxis: { type: 'value' },
      series: [{ data: Object.values(provinceCounts), type: 'bar' }],
    },
  })

  const genderCounts = data.value?.gender_counts || {}
  charts.push({
    el: 'genderChart',
    option: {
      tooltip: { trigger: 'item' },
      series: [{
        name: 'Gender', type: 'pie', radius: '60%',
        data: Object.entries(genderCounts).map(([name, value]) => ({ name, value })),
      }],
    },
  })

  const raceCounts = data.value?.race_counts || {}
  charts.push({
    el: 'raceChart',
    option: {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: Object.keys(raceCounts).map(k => k.split('_').map(s=>s[0].toUpperCase()+s.slice(1)).join(' ')) },
      yAxis: { type: 'value' },
      series: [{ data: Object.values(raceCounts), type: 'bar' }],
    },
  })

  const publicCounts = data.value?.public_counts || { public: 0, non_public: 0 }
  charts.push({
    el: 'publicChart',
    option: {
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: [
          { value: publicCounts.public || 0, name: 'Public (Published/Found)' },
          { value: publicCounts.non_public || 0, name: 'Non-public' },
        ],
      }],
    },
  })

  // Top submitters
  const top = data.value?.top_submitters || []
  charts.push({
    el: 'topSubmittersChart',
    option: {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: top.map(t => `User ${t.user_id}`) },
      yAxis: { type: 'value' },
      series: [{ data: top.map(t => t.count), type: 'bar' }],
    },
  })

  charts.forEach(({ el, option }) => {
    const container = document.getElementById(el)
    if (!container) return
    const existing = echarts.getInstanceByDom(container)
    if (existing) existing.dispose()
    const chart = echarts.init(container)
    chart.setOption(option)
  })

  // Simple resize listener
  const onResize = () => {
    const containers = document.querySelectorAll('[data-echart]')
    containers.forEach((c: any) => {
      const inst = echarts.getInstanceByDom(c)
      if (inst) inst.resize()
    })
  }
  window.addEventListener('resize', onResize)
  resizeObserver = () => window.removeEventListener('resize', onResize)
}

const formatPct = (n?: number | null) =>
  typeof n === 'number' ? `${(n * 100).toFixed(1)}%` : '—'

onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver()
  if (typeof window !== 'undefined' && (window as any).echarts) {
    const echarts = (window as any).echarts
    const containers = document.querySelectorAll('[data-echart]')
    containers.forEach((c: any) => {
      const inst = echarts.getInstanceByDom(c)
      if (inst) inst.dispose()
    })
  }
})
</script>

<template>
  <div class="space-y-4">
    <div v-if="error" class="rounded-md bg-red-50 p-3 text-red-700">{{ error }}</div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-6">
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="text-sm text-neutral-500">Total submissions</div>
        <div class="mt-1 text-2xl font-semibold">{{ data?.total_submissions ?? (loading ? '…' : 0) }}</div>
      </div>
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="text-sm text-neutral-500">Public cases</div>
        <div class="mt-1 text-2xl font-semibold">{{ data?.public_counts?.public ?? 0 }}</div>
      </div>
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="text-sm text-neutral-500">Found rate</div>
        <div class="mt-1 text-2xl font-semibold">{{ formatPct(data?.found_rate ?? 0) }}</div>
      </div>
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="text-sm text-neutral-500">Found alive</div>
        <div class="mt-1 text-2xl font-semibold">{{ data?.found_alive_count ?? 0 }}</div>
      </div>
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="text-sm text-neutral-500">Found dead</div>
        <div class="mt-1 text-2xl font-semibold">{{ data?.found_dead_count ?? 0 }}</div>
      </div>
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="text-sm text-neutral-500">Avg images / submission</div>
        <div class="mt-1 text-2xl font-semibold">{{ (data?.avg_images_per_submission ?? 0).toFixed(1) }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-3 lg:grid-cols-3">
      <div class="rounded-md border border-neutral-200 bg-white p-4 lg:col-span-2">
        <div class="mb-2 text-sm font-medium text-neutral-700">New submissions (last 12 months)</div>
        <div id="monthlyChart" data-echart class="h-64 w-full"></div>
      </div>
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="mb-2 text-sm font-medium text-neutral-700">Status distribution</div>
        <div id="statusChart" data-echart class="h-64 w-full"></div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-3 lg:grid-cols-2">
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="mb-2 text-sm font-medium text-neutral-700">By province</div>
        <div id="provinceChart" data-echart class="h-72 w-full"></div>
      </div>
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="mb-2 text-sm font-medium text-neutral-700">Public vs Non-public</div>
        <div id="publicChart" data-echart class="h-72 w-full"></div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-3 lg:grid-cols-2">
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="mb-2 text-sm font-medium text-neutral-700">Gender</div>
        <div id="genderChart" data-echart class="h-64 w-full"></div>
      </div>
      <div class="rounded-md border border-neutral-200 bg-white p-4">
        <div class="mb-2 text-sm font-medium text-neutral-700">Race</div>
        <div id="raceChart" data-echart class="h-64 w-full"></div>
      </div>
    </div>

    <div class="rounded-md border border-neutral-200 bg-white p-4">
      <div class="mb-2 text-sm font-medium text-neutral-700">Top submitters</div>
      <div id="topSubmittersChart" data-echart class="h-72 w-full"></div>
    </div>

    <div v-if="loading" class="rounded-md border border-neutral-200 bg-white p-6 text-center text-neutral-600">Loading…</div>
  </div>
</template>
