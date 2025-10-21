import { onMounted, onBeforeUnmount, ref, type Ref } from 'vue'
import { process } from 'std-env'

export type MouseSmokeOptions = {
  color?: string // rgb string like '255,255,255' or hex '#fff'
  maxPerMove?: number // particles per mousemove frame
  size?: [number, number] // [min, max] radius in px
  drift?: number // random velocity scale
  fade?: number // alpha decrement per frame (smaller = longer life)
  blur?: number // canvas shadow blur
  glow?: string // canvas shadow color
  zIndex?: number // canvas z-index
  throttleMs?: number // limit mouse spawn rate
}

type Particle = { x: number; y: number; a: number; r: number; dx: number; dy: number }
type ExcludeMode = 'spawn' | 'mask' | 'both'

export function useMouseSmoke(
  targetEl: Ref<HTMLElement | null>,
  exclude: Array<string | HTMLElement> = [],
  excludeMode: ExcludeMode = 'both',
  opts: MouseSmokeOptions = {}
) {
  const {
    color = '255,255,255',
    maxPerMove = 3,
    size = [10, 30],
    drift = 1,
    fade = 0.012,
    blur = 12,
    glow = 'rgba(99,102,241,0.35)',
    zIndex = 1,
    throttleMs = 16,
  } = opts

  const canvas = ref<HTMLCanvasElement | null>(null)
  const running = ref(true)
  let ctx: CanvasRenderingContext2D | null = null
  let particles: Particle[] = []
  let raf = 0
  let lastSpawn = 0

  // ---- exclusions helpers ----
  let excludedEls: HTMLElement[] = []
  let excludedRects: Array<DOMRect> = []

  const resolveExcluded = (): HTMLElement[] => {
    const host = targetEl.value
    if (!host) return []
    const list: HTMLElement[] = []
    for (const item of exclude) {
      if (typeof item === 'string') {
        host.querySelectorAll<HTMLElement>(item).forEach((el) => list.push(el))
      } else if (item instanceof HTMLElement) {
        list.push(item)
      }
    }
    return list
  }

  const isOverExcluded = (e: MouseEvent) => {
    if (!excludedEls.length) return false
    const path = e.composedPath() as EventTarget[]
    for (const t of path) {
      if (t instanceof HTMLElement) {
        for (const ex of excludedEls) if (t === ex || ex.contains(t)) return true
      }
    }
    return false
  }

  const updateExcludedRects = () => {
    excludedRects = excludedEls.map((el) => el.getBoundingClientRect())
  }

  const hexToRgb = (hex: string): string | null => {
    const m = hex.replace('#', '').match(/^([0-9a-f]{3}|[0-9a-f]{6})$/i)
    if (!m) return null
    //@ts-ignore
    let h = m[1].toLowerCase()
    if (h.length === 3)
      h = h
        .split('')
        .map((c) => c + c)
        .join('')
    const n = parseInt(h, 16)
    return `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`
  }
  const getColorRgb = (c: string) => (c.startsWith('#') ? (hexToRgb(c) ?? '255,255,255') : c)

  const resize = () => {
    const host = targetEl.value
    const c = canvas.value
    if (!host || !c) return
    const bounds = host.getBoundingClientRect()
    c.width = Math.max(1, Math.floor(bounds.width))
    c.height = Math.max(1, Math.floor(bounds.height))
    excludedEls = resolveExcluded()
    updateExcludedRects()
  }

  const addParticle = (x: number, y: number) => {
    const [minR, maxR] = size
    const r = Math.random() * (maxR - minR) + minR
    particles.push({
      x,
      y,
      r,
      a: 1,
      dx: (Math.random() - 0.5) * drift,
      dy: (Math.random() - 0.5) * drift,
    })
  }

  const onMove = (e: MouseEvent) => {
    const host = targetEl.value
    if (!host) return
    const now = performance.now()
    if (now - lastSpawn < throttleMs) return
    lastSpawn = now

    if ((excludeMode === 'spawn' || excludeMode === 'both') && isOverExcluded(e)) return

    const rect = host.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    for (let i = 0; i < maxPerMove; i++) addParticle(x, y)
  }

  const draw = () => {
    if (!running.value) return
    const c = canvas.value
    if (!c || !ctx) return

    ctx.clearRect(0, 0, c.width, c.height)

    const rgb = getColorRgb(color)
    ctx.shadowBlur = blur
    ctx.shadowColor = glow

    for (const p of particles) {
      ctx.fillStyle = `rgba(${rgb},${p.a})`
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fill()
      p.x += p.dx
      p.y += p.dy
      p.a -= fade
    }
    particles = particles.filter((p) => p.a > 0.02)

    // Mask out excluded rects so smoke never appears over them
    if ((excludeMode === 'mask' || excludeMode === 'both') && excludedRects.length) {
      const hostRect = targetEl.value!.getBoundingClientRect()
      ctx.save()
      ctx.globalCompositeOperation = 'destination-out'
      for (const r of excludedRects) {
        const x = r.left - hostRect.left
        const y = r.top - hostRect.top
        ctx.clearRect(x, y, r.width, r.height)
      }
      ctx.restore()
    }

    raf = requestAnimationFrame(draw)
  }

  const start = () => {
    running.value = true
    cancelAnimationFrame(raf)
    raf = requestAnimationFrame(draw)
  }
  const stop = () => {
    running.value = false
    cancelAnimationFrame(raf)
  }

  onMounted(() => {
    if (!process.client) return
    const host = targetEl.value
    if (!host) return

    if (getComputedStyle(host).position === 'static') {
      host.style.position = 'relative'
    }

    const c = document.createElement('canvas')
    c.style.position = 'absolute'
    c.style.inset = '0'
    c.style.pointerEvents = 'none'
    c.style.zIndex = String(zIndex)
    host.appendChild(c)
    canvas.value = c
    ctx = c.getContext('2d')

    excludedEls = resolveExcluded()
    resize()
    window.addEventListener('resize', resize)
    host.addEventListener('mousemove', onMove)
    start()
  })

  onBeforeUnmount(() => {
    stop()
    const host = targetEl.value
    const c = canvas.value
    window.removeEventListener('resize', resize)
    host?.removeEventListener('mousemove', onMove)
    if (c && host && c.parentElement === host) host.removeChild(c)
    canvas.value = null
    ctx = null
    particles = []
  })

  return { canvas, running, start, stop, resize }
}
